import os
import uuid

try:
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client
    from qcloud_cos.cos_exception import CosClientError, CosServiceError
    COS_AVAILABLE = True
except ImportError:
    COS_AVAILABLE = False
    CosConfig = None
    CosS3Client = None
    CosClientError = Exception
    CosServiceError = Exception

class COSClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(COSClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init_client(self):
        if self._initialized:
            return

        if not COS_AVAILABLE:
            raise ValueError("COS SDK 未安装")

        secret_id = os.environ.get('COS_SECRET_ID', '')
        secret_key = os.environ.get('COS_SECRET_KEY', '')
        region = os.environ.get('COS_REGION', 'ap-shanghai')
        bucket = os.environ.get('COS_BUCKET', '')

        if not secret_id or not secret_key or not bucket:
            raise ValueError("COS配置未完整设置，请检查环境变量")

        print(f"[COS] 初始化 - Bucket: {bucket}, Region: {region}")

        config = CosConfig(
            Region=region,
            SecretId=secret_id,
            SecretKey=secret_key
        )
        self.client = CosS3Client(config)
        self.bucket = bucket
        self.region = region
        self._initialized = True

    def upload_file(self, file_path, key=None):
        self._init_client()
        
        if key is None:
            ext = os.path.splitext(file_path)[1]
            key = f"uploads/{uuid.uuid4().hex}{ext}"
        
        try:
            self.client.upload_file(
                Bucket=self.bucket,
                LocalFilePath=file_path,
                Key=key
            )
            return {"key": key}
        except (CosClientError, CosServiceError) as e:
            raise Exception(f"上传文件到COS失败: {str(e)}")

    def upload_bytes(self, content, key=None, content_type='image/jpeg'):
        self._init_client()
        
        if key is None:
            ext = '.' + content_type.split('/')[-1] if '/' in content_type else '.bin'
            key = f"uploads/{uuid.uuid4().hex}{ext}"
        
        try:
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=content,
                Key=key,
                ContentType=content_type
            )
            return {"key": key, "etag": response.get('ETag', '')}
        except (CosClientError, CosServiceError) as e:
            raise Exception(f"上传数据到COS失败: {str(e)}")

    def delete_file(self, key):
        self._init_client()
        
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            return True
        except (CosClientError, CosServiceError) as e:
            raise Exception(f"删除COS文件失败: {str(e)}")

    def get_presigned_url(self, key, expires=3600):
        self._init_client()
        try:
            url = self.client.get_presigned_url(
                Method='GET',
                Bucket=self.bucket,
                Key=key,
                Expired=expires
            )
            return url
        except (CosClientError, CosServiceError) as e:
            raise Exception(f"生成签名URL失败: {str(e)}")

    def get_file_url(self, key):
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"

    def normalize_key(self, url_or_key):
        if not url_or_key:
            return None
        if url_or_key.startswith('http'):
            try:
                self._init_client()
                region = self.region if hasattr(self, 'region') else os.environ.get('COS_REGION', 'ap-shanghai')
                if f".cos.{region}.myqcloud.com/" in url_or_key:
                    return url_or_key.split(f".cos.{region}.myqcloud.com/")[-1]
            except Exception:
                pass
            return url_or_key
        return url_or_key

cos_client = COSClient()