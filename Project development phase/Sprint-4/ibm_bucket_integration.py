from ibm_botocore.client import Config,ClientError
import ibm_boto3


COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID = "FC1y4xKQnZvEhpXhxunyG9el68AsdmaS5oz1gBJx90_g"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/9149c137cf2d470299201354c3c033ff:8db985c4-dc1b-49ac-86db-33a9d5e272ae::"
public_url = "https://cloud-object-storage-6y-cos-standard-m3z.s3.jp-tok.cloud-object-storage.appdomain.cloud/"

cos = ibm_boto3.resource(
    "s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

def get_bucket_contents(bucket_name):
    print("Retrieving bucket contents from: {0}".format(bucket_name))
    try:
        files = cos.Bucket(bucket_name).objects.all()
        for file in files:
            print(file.url)
            print("Item: {0} ({1} bytes).".format(file.key, file.size))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve bucket contents: {0}".format(e))
    return files
get_bucket_contents("cloud-object-storage-6y-cos-standard-m3z")

def get_item(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    try:
        file = cos.Object(bucket_name, item_name).get()
        print(file.key)
        print("File Contents: {0}".format(file["Body"].read()))
        
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))
    return file

def multi_part_upload(bucket_name, item_name, file_data):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        part_size = 1024 * 1024 * 5
        file_threshold = 1024 * 1024 * 15
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )
        cos.Object(bucket_name, item_name).upload_fileobj(
            Fileobj=file_data,
            Config=transfer_config
        )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))
    return public_url+item_name