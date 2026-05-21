from pathlib import Path
import sys
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent
repo_root = backend_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv(backend_root / ".env")

import backend.adapters.utils as dataset_utils

sys.modules.setdefault("adapters.utils", dataset_utils)

from backend.adapters.dataset import S3AudioClassificationDataset
from backend.storage.client import DATA_BUCKET, s3_client

dataset_prefix = "default/test/"

response = s3_client.list_objects_v2(Bucket=DATA_BUCKET, Prefix=dataset_prefix)
file_to_class_mapping = {
    obj["Key"]: obj["Key"][len(dataset_prefix):].split("/", 1)[0]
    for obj in response.get("Contents", [])
    if obj["Key"].lower().endswith(".wav")
}
class_mapping = {
    class_name: idx
    for idx, class_name in enumerate(sorted(set(file_to_class_mapping.values())))
}

dataset = S3AudioClassificationDataset(
    file_to_class_mapping=file_to_class_mapping,
    sample_rate=16000,
    class_mapping=class_mapping,
)

dataset.__getitem__(1)