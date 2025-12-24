"""
Cloud Storage Handler for Medical Images

Supports:
- Local file storage (development)
- AWS S3 (production)
- Cloudinary (alternative)

Usage:
    from storage import storage_handler
    
    # Upload file
    url = await storage_handler.upload_file(file_data, filename, content_type)
    
    # Delete file
    await storage_handler.delete_file(file_path)
"""

import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
from abc import ABC, abstractmethod


class StorageHandler(ABC):
    """Abstract base class for storage handlers"""
    
    @abstractmethod
    async def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file and return URL"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file"""
        pass


class LocalStorageHandler(StorageHandler):
    """Local filesystem storage (for development)"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Save file to local directory"""
        # Generate unique filename
        ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        # Return relative path
        return str(file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local directory"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Return file path (for local access)"""
        return file_path


class S3StorageHandler(StorageHandler):
    """AWS S3 storage (for production)"""
    
    def __init__(self):
        try:
            import boto3
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.bucket_name = os.getenv('AWS_S3_BUCKET')
            
            if not self.bucket_name:
                raise ValueError("AWS_S3_BUCKET environment variable not set")
            
            print(f"✅ AWS S3 storage initialized (bucket: {self.bucket_name})")
            
        except ImportError:
            raise RuntimeError(
                "boto3 not installed. Install with: pip install boto3"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 storage: {e}")
    
    async def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to S3"""
        # Generate unique key
        ext = Path(filename).suffix
        key = f"scans/{uuid.uuid4()}{ext}"
        
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_data,
            ContentType=content_type,
            ACL='private'  # Keep files private
        )
        
        # Return S3 path
        return key
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except Exception as e:
            print(f"Error deleting S3 file: {e}")
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Generate presigned URL for private file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return ""


class CloudinaryStorageHandler(StorageHandler):
    """Cloudinary storage (alternative to S3)"""
    
    def __init__(self):
        try:
            import cloudinary
            import cloudinary.uploader
            
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key=os.getenv('CLOUDINARY_API_KEY'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET')
            )
            
            self.cloudinary = cloudinary
            print("✅ Cloudinary storage initialized")
            
        except ImportError:
            raise RuntimeError(
                "cloudinary not installed. Install with: pip install cloudinary"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Cloudinary: {e}")
    
    async def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to Cloudinary"""
        import io
        
        # Upload to Cloudinary
        result = self.cloudinary.uploader.upload(
            io.BytesIO(file_data),
            folder="breast_cancer_scans",
            resource_type="image",
            format="jpg"
        )
        
        # Return public ID
        return result['public_id']
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            self.cloudinary.uploader.destroy(file_path)
            return True
        except Exception as e:
            print(f"Error deleting Cloudinary file: {e}")
            return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Get Cloudinary URL"""
        return self.cloudinary.CloudinaryImage(file_path).build_url()


# ============================================================================
# STORAGE FACTORY
# ============================================================================

def get_storage_handler() -> StorageHandler:
    """Get appropriate storage handler based on environment"""
    storage_type = os.getenv('STORAGE_TYPE', 'local').lower()
    
    if storage_type == 's3':
        try:
            return S3StorageHandler()
        except Exception as e:
            print(f"⚠️  Failed to initialize S3, falling back to local: {e}")
            return LocalStorageHandler()
    
    elif storage_type == 'cloudinary':
        try:
            return CloudinaryStorageHandler()
        except Exception as e:
            print(f"⚠️  Failed to initialize Cloudinary, falling back to local: {e}")
            return LocalStorageHandler()
    
    else:  # 'local' or default
        upload_dir = os.getenv('UPLOAD_DIR', './uploads')
        return LocalStorageHandler(upload_dir)


# Global storage handler instance
storage_handler = get_storage_handler()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def save_uploaded_file(file_data: bytes, filename: str, content_type: str) -> str:
    """
    Save uploaded file using configured storage handler
    
    Args:
        file_data: File binary data
        filename: Original filename
        content_type: MIME type
    
    Returns:
        str: File path or URL
    """
    return await storage_handler.upload_file(file_data, filename, content_type)


async def delete_uploaded_file(file_path: str) -> bool:
    """
    Delete uploaded file
    
    Args:
        file_path: Path or URL of file to delete
    
    Returns:
        bool: Success status
    """
    return await storage_handler.delete_file(file_path)


async def get_file_access_url(file_path: str) -> str:
    """
    Get accessible URL for file
    
    Args:
        file_path: Stored file path
    
    Returns:
        str: Public or presigned URL
    """
    return await storage_handler.get_file_url(file_path)

