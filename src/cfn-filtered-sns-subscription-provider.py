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
            'TopicArn': self.get('TopicArn')
        }
        return args

    def set_return_attributes(self, response):
        pass

    def create(self):
        try:
            args = self.create_arguments()
            response = self.sns.subscribe(**args)
            self.set_return_attributes(response)
        except ClientError as e:
            self.physical_resource_id = 'could-not-create'
            self.fail('{}'.format(e))

    def update(self):
        if self.get_old('Name', self.get('Name')) != self.get('Name'):
            self.fail('Cannot change the name of a secret')
            return

        try:
            args = self.create_arguments()
            args['SecretId'] = self.physical_resource_id
            del args['Name']
            del args['Tags']

            response = self.sm.update_secret(**args)
            self.set_return_attributes(response)

            if self.get_old('Tags', self.get('Tags')) != self.get('Tags'):
                if len(self.get_old('Tags')) > 0:
                    self.sm.untag_resource(SecretId=self.physical_resource_id,
                                           TagKeys=list(map(lambda t: t['Key'], self.get_old('Tags'))))
                self.sm.tag_resource(SecretId=self.physical_resource_id, Tags=self.get('Tags'))

        except ClientError as e:
            self.fail('{}'.format(e))

    def delete(self):
        if re.match(r'^arn:aws:secretsmanager:.*', self.physical_resource_id):
            try:
                self.sm.delete_secret(SecretId=self.physical_resource_id,
                                      RecoveryWindowInDays=self.get('RecoveryWindowInDays'))
                self.success('Secret with the name %s is scheduled for deletion' % self.get('Name'))
            except ClientError as e:
                if e.response["Error"]["Code"] != 'ResourceNotFoundException':
                    self.fail('{}'.format(e))
        else:
            self.success('Delete request for secret with the name {} is ignored'.format(self.get('Name')))


provider = SecretsManagerSecretProvider()


def handler(request, context):
    return provider.handle(request, context)
