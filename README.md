# s3script: a fast, flexible way to process object metadata on s3

# Setup

```
python3 -m venv .virtualenv # to deactivate the environment type "deactivate" when you're done
source .virtualenv/bin/activate
pip3 install -r requirements.txt
```

# Usage

```
usage: s3script.py [-h] [--sqsqueue SQSQUEUE] [--snstopic SNSTOPIC]
                   [--region REGION] [--context CONTEXT]
                   s3path template
```

# Templates

Templates are generic moustache templates. The s3 [ObjectSummary](http://boto3.readthedocs.org/en/latest/reference/services/s3.html#objectsummary) is made available through the object variable. You may access fields of ```ObjectSummary``` as you would normally in any moustache template (object.field). This is an example template for an s3 event notification (it is also builtin with this script and made available via the templates directory):

```
{
   "Records": [
   {
      "eventVersion": "2.0",
         "eventSource": "aws:s3",
         "awsRegion": "{{region}}",
         "eventTime": "{{date}}",
         "eventName": "ObjectCreated:Put",
         "s3": {
            "s3SchemaVersion": "1.0",
            "bucket": {
               "name": "{{object.bucket_name}}",
               "arn": "arn:aws:s3:::{{object.bucket_name}}"
            },
            "object": {
               "key": "{{object.key}}",
               "size": {{object.size}},
               "eTag": {{&object.e_tag}}
            }
         }
   }
   ]
}
```

# Examples
## Emulating s3 event notifications (aka s3 touch)
```
python3 s3script.py --region us-east-1 --context date=THISISADATE --context region=THISISAREGION s3://SOMEBUCKET/SOMEFILE.gz templates/s3eventnotification.template 
>> processing SOMEFILE.gz
{
   "Records": [
   {
      "eventVersion": "2.0",
         "eventSource": "aws:s3",
         "awsRegion": "THISISAREGION",
         "eventTime": "THISISADATE",
         "eventName": "ObjectCreated:Put",
         "s3": {
            "s3SchemaVersion": "1.0",
            "bucket": {
               "name": "SOMEBUCKET",
               "arn": "arn:aws:s3:::r7sonardata"
            },
            "object": {
               "key": "SOMEFILE.gz",
               "size": 3883,
               "eTag": "c9074428c901a4c3d6f09607212e6bb7"
            }
         }
   }
   ]
```

Try taking the above example and using ```--sqsqueue queuename``` to send the body (content after the ```>> processing``` line) directly to an sqs queue of your choice.
