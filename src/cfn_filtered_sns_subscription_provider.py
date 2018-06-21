import json
import logging
import os
import re

import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider

log = logging.getLogger()
log.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

request_schema = {
    "type": "object",
    "required": ["Protocol", "TopicArn", "TopicArn"],
    "properties": {
        "Protocol": {
            "type": "string",
            "description": "The sns protocol"
        },
        "Endpoint": {
            "type": "string",
            "description": "The sns destination"
        },
        "TopicArn": {
            "type": "string",
            "description": "SNS Topic ARN"
        },
        "FilterPolicy": {
            "type": "object",
            "description": "SNS Filter policy"
        }
    }
}


class FilteredSnsSubscriptionProvider(ResourceProvider):

    def __init__(self):
        super(FilteredSnsSubscriptionProvider, self).__init__()
        self._value = None
        self.request_schema = request_schema
        self.sns = boto3.client('sns')
        self.region = boto3.session.Session().region_name
        self.account_id = (boto3.client('sts')).get_caller_identity()['Account']

    def convert_property_types(self):
        pass

    def create_arguments(self):
        args = {
            'Protocol': self.get('Protocol'),
            'Endpoint': self.get('Endpoint'),
            'TopicArn': self.get('TopicArn'),
            'ReturnSubscriptionArn': True,
            'Attributes': {
                'FilterPolicy': json.dumps(self.get('FilterPolicy'))
            }
        }
        return args

    def set_return_attributes(self, response):
        self.physical_resource_id = response['SubscriptionArn']

    def has_changed(self, property_name):
        return self.get_old('property_name', self.get('property_name')) != self.get('property_name')

    def needs_recreate(self):
        return self.has_changed('Protocol') or self.has_changed('Endpoint') or self.has_changed('TopicArn')

    def create(self):
        try:
            args = self.create_arguments()
            response = self.sns.subscribe(**args)
            self.set_return_attributes(response)
        except ClientError as e:
            self.physical_resource_id = 'could-not-create'
            self.fail('{}'.format(e))

    def update(self):
        if self.needs_recreate():
            self.delete()
            self.create()
        else:
            try:
                args = {
                    'SubscriptionArn': self.physical_resource_id,
                    'AttributeName': 'FilterPolicy',
                    'AttributeValue': json.dumps(self.get('FilterPolicy'))
                }
                self.sns.set_subscription_attributes(**args)
            except ClientError as e:
                self.fail('{}'.format(e))

    def delete(self):
        try:
            self.sns.unsubscribe(SubscriptionArn=self.physical_resource_id)
            self.success('Subscription deleted: {}'.format(self.physical_resource_id))
        except ClientError as e:
            if e.response["Error"]["Code"] != 'ResourceNotFoundException':
                self.fail('{}'.format(e))


provider = FilteredSnsSubscriptionProvider()


def handler(request, context):
    return provider.handle(request, context)
