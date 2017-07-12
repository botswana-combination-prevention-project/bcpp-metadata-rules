from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings


class AppConfig(DjangoAppConfig):
    name = 'bcpp_metadata_rules'


if settings.APP_NAME == 'bcpp_metadata_rules':
    from edc_metadata.apps import AppConfig as MetadataAppConfig

    class EdcMetadataAppConfig(MetadataAppConfig):
        reason_field = {'bcpp_metadata_rules.subjectvisit': 'reason'}
