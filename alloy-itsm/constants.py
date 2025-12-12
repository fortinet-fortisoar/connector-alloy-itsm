"""
Copyright start
MIT License
Copyright (c) 2025 Fortinet Inc
Copyright end
"""

LOGGER_NAME = 'alloy-itsm'

# API Endpoints
ENDPOINTS = {
    'profile': '/profile',
    'token': '/token',
    'objects': '/{object_class}',
    'objects_advanced': '/v2/{object_class}',
    'object_by_id': '/v2/object/{oid}',
    'activities': '/v2/Activities/{oid}',
    'activities_advanced': '/v2/Activities/{oid}',
    'dictionary': '/v2/Dictionary',
    'dictionary_advanced': '/v2/Dictionary',
    'create_object': '/v2',
    'step_action': '/v2/object/{oid}/action/{action_id}',
    'step_action_check': '/v2/object/{oid}/action/{action_id}/check',
    # Attachment Endpoints
    'list_attachments': '/v2/Object/{oid}/Attachments',
    'get_attachment_content': '/v2/Object/{oid}/Attachments/{attachment_id}/content',
    'download_attachment': '/v2/Object/{oid}/Attachments/{attachment_id}/download',
    'add_attachments': '/v2/Object/{oid}/Attachments',
    'remove_attachment': '/v2/Object/{oid}/Attachments/{attachment_id}',
    'update_attachment_description': '/v2/Object/{oid}/Attachments/{attachment_id}'
}

# API Version prefix (if needed for future use)
API_VERSION_V2 = '/v2'
