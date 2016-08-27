#!/usr/local/bin/python3

import boto3
import sys
import argparse
import re
import json
import pystache
from datetime import date

class StdoutMessenger():
   def message(self, body):
      print(body, end="")

   def close(self):
      pass

   def flush(self):
      pass

class SQSMessenger():
   queue = None
   messages = []
   msgcount = 0

   def __init__(self, queue, region):
      client = boto3.resource("sqs", region)
      self.queue = client.get_queue_by_name(QueueName=queue)
   
   def message(self, body):
      self.messages.append({"Id": str(self.msgcount), "MessageBody": body})
      self.msgcount += 1
      if len(self.messages) % 10 == 0:
         self.flush()

   def close(self):
      self.flush()
      pass

   def flush(self):
      if len(self.messages) > 0:
         resp = self.queue.send_messages(Entries=self.messages)
         if "Failed" in resp and len(resp["Failed"]) > 0:
            print("FAILURE: %s", json.dumps(resp["Failed"]), file=sys.stderr)
         self.messages = []

class SNSMessenger():
   topic = None

   def __init__(self, topic, region):
      client = boto3.resource("sns", region)
      self.topic = client.get_topic_by_name(TopicName=topic)

   def message(self, body):
      self.topic.publish(MessageBody=body)

   def close(self):
      pass

   def flush(self):
      pass

def main():
   parser = argparse.ArgumentParser(description="Emulates s3 event notifications for a set of s3 objects")
   parser.add_argument("s3path", help="the s3 path (bucket/key)")
   parser.add_argument("template", help="the moustache message template")
   parser.add_argument("--sqsqueue", help="Specifies the sqs queue to send to. Must not be used with --sns")
   parser.add_argument("--snstopic", help="Specifies the sns topic to publish to. Must not be used with --sqs")
   parser.add_argument("--region", default="us-east-1", help="Specifies the aws region to use (for sqs or sns)")
   parser.add_argument("--context", action="append", type=lambda kv: kv.split("="), dest="context", help="Specify additional name=value pairs to pass to the template")
   args = parser.parse_args()

   if args.sqsqueue and args.snstopic:
      print("error: only one of --sqsqueue or --snstopic must be supplied")

   bucket_match = re.search(r"^s3://(?P<bucket>[^/]+)/(?P<key>.*)$", args.s3path)
   if not bucket_match:
      raise RuntimeError("s3 path must be in the format s3://<bucket>/<key>")

   context = {}
   if args.context:
      context = dict(args.context)

   with open(args.template, 'r') as template:
      template_data = template.read()

   if args.sqsqueue:
      messenger = SQSMessenger(args.sqsqueue, args.region)
   elif args.snstopic:
      messenger = SNSMessenger(args.snsqueue, args.region)
   else:
      messenger = StdoutMessenger()

   renderer = pystache.Renderer()
   s3 = boto3.resource("s3")
   bucket = s3.Bucket(bucket_match.group("bucket"))
   for obj in bucket.objects.filter(Prefix=bucket_match.group("key")):
      print(">> processing %s" % obj.key)
      context["object"] = obj
      messenger.message(renderer.render(template_data, context))

   messenger.close()

if __name__ == "__main__":
   main()
