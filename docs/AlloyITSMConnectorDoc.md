## About the connector

Alloy ITSM is an IT Service Management (ITSM) solution designed to help organizations manage and streamline their IT
services and operations. This connector is designed to manage and automate ticket-based operations.
<p>This document provides information about the Alloy ITSM Connector, which facilitates automated interactions, with a Alloy ITSM server using FortiSOAR&trade; playbooks. Add the Alloy ITSM Connector as a step in FortiSOAR&trade; playbooks and perform automated operations with Alloy ITSM.</p>

### Version information

Connector Version: 1.0.0

Contributor: amey-spryiq

Authored By: Fortinet

Certified: No

## Installing the connector

<p>Use the <strong>Connector Store</strong> to install the connector. For the detailed procedure to install a connector, click <a href="https://docs.fortinet.com/document/fortisoar/0.0.0/installing-a-connector/1/installing-a-connector" target="_top">here</a>.<br>You can also use the following <code>yum</code> command to install connectors from an SSH session:</p>

```
sudo yum install cyops-connector-alloy-itsm
```

## Prerequisites to configuring the connector

- You must have the URL of Alloy ITSM server to which you will connect and perform automated operations and credentials
  to access that server.
- The FortiSOAR&trade; server should have outbound connectivity to port 443 on the Alloy ITSM server.

## Minimum Permissions Required

- N/A

## Configuring the connector

For the procedure to configure a connector,
click [here](https://docs.fortinet.com/document/fortisoar/0.0.0/configuring-a-connector/1/configuring-a-connector)

### Configuration parameters

<p>In FortiSOAR&trade;, on the Connectors page, click the <strong>Alloy ITSM</strong> connector row (if you are in the <strong>Grid</strong> view on the Connectors page) and in the <strong>Configurations</strong> tab enter the required configuration details:</p>
<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Server URL<br></td><td>Specify the URL of the Alloy Navigator Express server to connect and perform automated operations.<br>
<tr><td>Get Access Token<br></td><td>Select the account type from the following options: "Application Account" or "Technician Account." By default, "Application Account" is selected.<br>
<strong>If you choose 'Application Account'</strong><ul><li>Client ID: Specify the client ID retrieved from the Alloy Navigator Express application settings.</li><li>Client Secret: Specify the client secret retrieved from the Alloy Navigator Express application settings.</li></ul><strong>If you choose 'Technician Account'</strong><ul><li>Username: Specify the username for the Alloy Navigator Express technician account.</li><li>Password: Specify the password for the Alloy Navigator Express technician account.</li></ul></td></tr><tr><td>Verify SSL<br></td><td>Specifies whether the SSL certificate for the server is to be verified or not. <br/>By default, this option is set as True.<br></td></tr>
</tbody></table>

## Actions supported by the connector

The following automated operations can be included in playbooks and you can also use the annotations to access
operations:
<table border=1><thead><tr><th>Function<br></th><th>Description<br></th><th>Annotation and Category<br></th></tr></thead><tbody><tr><td>Get Current User Profile<br></td><td>Retrieve details about the currently logged-in user or technician from Alloy Navigator Express.<br></td><td>get_current_user_profile <br/>Investigation<br></td></tr>
<tr><td>Get Objects<br></td><td>Retrieve objects from the selected Alloy Navigator class while applying filters, sort criteria, and pagination parameters.<br></td><td>get_objects <br/>Investigation<br></td></tr>
<tr><td>Get Objects Advanced Search<br></td><td>Retrieve Alloy Navigator objects using advanced filtering operators. Supports complex queries without URL length restrictions.<br></td><td>get_objects_advanced <br/>Investigation<br></td></tr>
<tr><td>Get Object By ID<br></td><td>Retrieve all fields of a specific object by using its OID or database ID.<br></td><td>get_object_by_id <br/>Investigation<br></td></tr>
<tr><td>Get Object Activities<br></td><td>Retrieve the activity or history records for a specific Alloy Navigator object using the filter parameters you provide.<br></td><td>get_object_activities <br/>Investigation<br></td></tr>
<tr><td>Advanced Search for Object Activities<br></td><td>Retrieve object activities using POST method with advanced filtering operators (=, <>, >, >=, <, <=). Supports complex queries without URL length limitations.<br></td><td>get_object_activities_advanced <br/>Investigation<br></td></tr>
<tr><td>Get Classification Values<br></td><td>Retrieve classification or dictionary values for Alloy Navigator objects using the filter parameters you’ve provided.<br></td><td>get_classification_values <br/>Investigation<br></td></tr>
<tr><td>Advanced Search for Classification Values<br></td><td>Retrieve classification/dictionary values using POST method with advanced filtering operators (=, <>, >, >=, <, <=). Supports complex queries without URL length limitations.<br></td><td>get_classification_values_advanced <br/>Investigation<br></td></tr>
<tr><td>Create Object<br></td><td>Creates a new Alloy Navigator object record using a workflow Create Action. This action is not supported for Service Requests; use the Submit Request action for Service Catalog Items instead.<br></td><td>create_object <br/>Investigation<br></td></tr>
<tr><td>Update Object<br></td><td>Run a workflow Step Action on an Alloy Navigator object to update fields or trigger workflows. Cannot be used for Software Catalog and Stock Room objects.<br></td><td>run_step_action <br/>Investigation<br></td></tr>
<tr><td>Check Step Action Availability<br></td><td>Check whether the workflow Step Action is available for the object according to the parameter you have entered.<br></td><td>check_step_action_availability <br/>Investigation<br></td></tr>
<tr><td>List Object Attachments<br></td><td>Retrieve a list of attachments for a specific Alloy Navigator object using the object ID and any additional filter parameters you have specified.<br></td><td>list_object_attachments <br/>Investigation<br></td></tr>
<tr><td>Get Attachment Content<br></td><td>Retrieve the base64-encoded content of a specific object attachment from Alloy Navigator Express.<br></td><td>get_attachment_content <br/>Investigation<br></td></tr>
<tr><td>Download Attachment<br></td><td>Download a specific object attachment from Alloy Navigator Express as binary data (base64-encoded for transfer).<br></td><td>download_attachment <br/>Investigation<br></td></tr>
<tr><td>Add Attachments<br></td><td>Add file attachments or links from FortiSOAR to a specific Alloy Navigator object using its object ID.<br></td><td>add_attachments <br/>Investigation<br></td></tr>
<tr><td>Remove Attachment<br></td><td>Remove a specific attachment from an Alloy Navigator object using the object ID and attachment ID you provided.<br></td><td>remove_attachment <br/>Investigation<br></td></tr>
<tr><td>Update Attachment Description<br></td><td>Update the description of a specific attachment in Alloy Navigator Express using the object ID, attachment ID, and the new description you provided.<br></td><td>update_attachment_description <br/>Investigation<br></td></tr>
</tbody></table>

### operation: Get Current User Profile

#### Input parameters

None.

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Items": [
            {
                "name": "",
                "caption": "",
                "value": ""
            }
        ]
    },
    "user_info": {
        "id": "",
        "first_name": "",
        "last_name": "",
        "full_name": "",
        "organization": "",
        "is_technician": "",
        "available_now": "",
        "address": "",
        "gender": ""
    }
}
```

### operation: Get Objects

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Class<br></td><td>Specify the name of the object class from which you want to retrieve objects in Alloy Navigator Express. Note: For the correct spelling of Alloy Navigator Express object class names, see https://docs.alloysoftware.com/alloynavigatorexpress/docs/api-userguide/api-userguide/supported-alloy-navigator-object-classes.htm#supported-alloy-navigator-express-object-classes<br>
</td></tr><tr><td>Fields<br></td><td>Specify a comma-separated list of field names to include in the output. If omitted, all available fields will be returned.<br>
</td></tr><tr><td>Search Text<br></td><td>Specify the search string used to filter the retrieved objects. Partial text fragments or keywords are allowed. Note: The search is performed on commonly used text fields that store key information, and each object class has its own set of these fields. For details: https://docs.alloysoftware.com/alloynavigatorexpress/help/webportal/content/common-functions/search/frequently-used-text-fields.htm<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the object search.<br>
</td></tr><tr><td>Sort By<br></td><td>Select the sorting direction. You may use only one parameter either "Sort Ascending" or "Sort Descending" parameter.<br>
<strong>If you choose 'Sort Ascending'</strong><ul><li>Sort Ascending: Specify the comma-separated fields to be used for ascending sorting.</li></ul><strong>If you choose 'Sort Descending'</strong><ul><li>Sort Descending: Specify the comma-separated fields to be used for descending sorting.</li></ul></td></tr></td></tr>
<tr><td>Limit<br></td><td>Specifies how many records should be returned. Use with the "Offset" parameter to enable pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Get Objects Advanced Search

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Class<br></td><td>Specify the name of the object class from which you want to retrieve objects in Alloy Navigator Express. Note: For the correct spelling of Alloy Navigator Express object class names, see https://docs.alloysoftware.com/alloynavigatorexpress/docs/api-userguide/api-userguide/supported-alloy-navigator-object-classes.htm#supported-alloy-navigator-express-object-classes<br>
</td></tr><tr><td>Fields<br></td><td>Specify a comma-separated list of field names to include in the output. If omitted, all available fields will be returned.<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the object advanced search. (e.g., [{"name":"Original_Cost","value":"100","operation":">"}])<br>
</td></tr><tr><td>Search Text<br></td><td>Specify the search string used to filter the retrieved objects. Partial text fragments or keywords are allowed. Note: The search is performed on commonly used text fields that store key information, and each object class has its own set of these fields. For details: https://docs.alloysoftware.com/alloynavigatorexpress/help/webportal/content/common-functions/search/frequently-used-text-fields.htm<br>
</td></tr><tr><td>Sort<br></td><td>Specifies the field on which the sorting operation is based. Defines the sorting order, either ascending (asc) or descending (desc). (e.g., [{"property":"OID","direction":"asc"}])<br>
</td></tr><tr><td>Limit<br></td><td>Specifies how many records should be returned. Use with the "Offset" parameter to enable pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Get Object By ID

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID or ID)<br></td><td>Specify the object identifier to retrieve details from Alloy Navigator Express. Object identifier - can be OID (e.g., T000002) or database GUID (e.g., {EB6D7E24-59CA-4532-B365-451724A7B880})<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Items": [
            {
                "name": "",
                "caption": "",
                "value": ""
            }
        ]
    }
}
```

### operation: Get Object Activities

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to retrieve object activities details from Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, COMP000123 for computers)<br>
</td></tr><tr><td>Activity Fields<br></td><td>Provide a comma-separated list of activity field names to include in the output. If omitted, all available fields will be returned. For e.g., Num,Details,Activity,Created_Date<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the object search. For e.g., {"Activity":"New Technical Issue was created"}<br>
</td></tr><tr><td>Sort By<br></td><td>Select the sorting direction. You may use only one parameter either "Sort Ascending" or "Sort Descending" parameter.<br>
<strong>If you choose 'Sort Ascending'</strong><ul><li>Sort Ascending: Specify the comma-separated fields to be used for ascending sorting.</li></ul><strong>If you choose 'Sort Descending'</strong><ul><li>Sort Descending: Specify the comma-separated fields to be used for descending sorting.</li></ul></td></tr></td></tr>
<tr><td>Limit<br></td><td>Specifies how many records should be returned. Use with the "Offset" parameter to enable pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Advanced Search for Object Activities

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to retrieve details from Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, COMP000123 for computers)<br>
</td></tr><tr><td>Activity Fields<br></td><td>Provide a comma-separated list of activity field names to include in the output. If omitted, all available fields will be returned. For e.g., ["Num","Details","Activity","Created_Date"]<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the object search. For e.g., [{"name":"Created_Date","value":"2019-12","operation":"="}]<br>
</td></tr><tr><td>Sort<br></td><td>Specifies the field on which the sorting operation is based. Defines the sorting order, either ascending (asc) or descending (desc). (e.g., [{"property":"Num","direction":"desc"}])<br>
</td></tr><tr><td>Limit<br></td><td>Specifies how many records should be returned. Use with the "Offset" parameter to enable pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

```
The output contains the following populated JSON schema:
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Get Classification Values

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Class<br></td><td>Specify the name of the object class from which you want to retrieve classification values in Alloy Navigator Express. Note: For the correct spelling of Alloy Navigator Express object class names, see https://docs.alloysoftware.com/alloynavigatorexpress/docs/api-userguide/api-userguide/supported-alloy-navigator-object-classes.htm#supported-alloy-navigator-express-object-classes<br>
</td></tr><tr><td>Reference Field<br></td><td>Specify a comma-separated list of reference field names to include in the output. For e.g. Status, Types, Priority, Category<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the classification values. (e.g., {"Rank":"3"})<br>
</td></tr><tr><td>Fields<br></td><td>Specify a comma-separated list of field names to include in the output. If omitted, all available fields will be returned. For e.g., Rank,Status,Description, etc.<br>
</td></tr><tr><td>Sort By<br></td><td>Select the sorting direction. You may use only one parameter either "Sort Ascending" or "Sort Descending" parameter.<br>
<strong>If you choose 'Sort Ascending'</strong><ul><li>Sort Ascending: Specify the comma-separated fields to be used for ascending sorting.</li></ul><strong>If you choose 'Sort Descending'</strong><ul><li>Sort Descending: Specify the comma-separated fields to be used for descending sorting.</li></ul></td></tr></td></tr>
<tr><td>Limit<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Advanced Search for Classification Values

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Class<br></td><td>Specify the name of the object class from which you want to retrieve classification values in Alloy Navigator Express. Note: For the correct spelling of Alloy Navigator Express object class names, see https://docs.alloysoftware.com/alloynavigatorexpress/docs/api-userguide/api-userguide/supported-alloy-navigator-object-classes.htm#supported-alloy-navigator-express-object-classes<br>
</td></tr><tr><td>Reference Field<br></td><td>Specify a comma-separated list of reference field names to include in the output. For e.g. Status, Types, Priority, Category<br>
</td></tr><tr><td>Fields<br></td><td>Specify a comma-separated list of field names to include in the output. If omitted, all available fields will be returned. For e.g., ["Rank","Status","Description"].<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the classification values. (e.g., [{"name":"Rank","value":"1","operation":">"}])<br>
</td></tr><tr><td>Sort<br></td><td>Specifies the field on which the sorting operation is based. Defines the sorting order, either ascending (asc) or descending (desc). (e.g., [{"property":"Rank","direction":"asc"}])<br>
</td></tr><tr><td>Limit<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Create Object

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Action ID<br></td><td>Specify the ID of the Create Action you want to use to create the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Summary<br></td><td>Specify the summary to use when creating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Description<br></td><td>Specify the description to use when creating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Category<br></td><td>Specify the category to use when creating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Requester<br></td><td>Specify the requester name or identifier to use when creating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Urgency<br></td><td>Select the urgency level to use when creating the object in Alloy Navigator Express. You can choose from the available options such as "1 - Immediate", "2 - Moderate", or "3 - No Rush".<br>
</td></tr><tr><td>Impact<br></td><td>Select the impact to use when creating the object in Alloy Navigator Express. You can choose from the available options such as "1 - Entire Location", "2 - Multiple People", or "3 - Single Person".<br>
</td></tr><tr><td>Additional Fields<br></td><td>Additional properties (fields), in the JSON format, based on which you want to the object in Alloy Navigator Express.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Succeed": "",
        "ObjectID": "",
        "ObjectOID": ""
    }
}
```

### operation: Update Object

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to update object details in Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, V000006 for vendors, COMP000123 for computers)<br>
</td></tr><tr><td>Step Action ID<br></td><td>Specify the ID of the step action you want to use to update the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Summary<br></td><td>Specify the summary to use when updating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Description<br></td><td>Specify the description to use when updating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Category<br></td><td>Specify the category to use when updating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Requester<br></td><td>Specify the requester name or identifier to use when updating the object in Alloy Navigator Express.<br>
</td></tr><tr><td>Urgency<br></td><td>Select the urgency level to use when updating the object in Alloy Navigator Express. You can choose from the available options such as "1 - Immediate", "2 - Moderate", or "3 - No Rush".<br>
</td></tr><tr><td>Impact<br></td><td>Select the impact to use when updating the object in Alloy Navigator Express. You can choose from the available options such as "1 - Entire Location", "2 - Multiple People", or "3 - Single Person".<br>
</td></tr><tr><td>Additional Fields<br></td><td>Additional properties (fields), in the JSON format, based on which you want to the object in Alloy Navigator Express.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Succeed": "",
        "ObjectID": "",
        "ObjectOID": ""
    }
}
```

### operation: Check Step Action Availability

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to check the action availability in Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, V000006 for vendors, COMP000123 for computers)<br>
</td></tr><tr><td>Step Action ID<br></td><td>Specify the ID of the step action to check the action availability in Alloy Navigator Express.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Result": ""
    },
    "action_available": "",
    "availability_message": ""
}
```

### operation: List Object Attachments

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to retrieve object attachments from Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, or GUID like {6D978EE7-...})<br>
</td></tr><tr><td>Fields<br></td><td>Specify a comma-separated list of attachment field names to include in the output. If omitted, all available fields will be returned. For e.g. ID,Name,Created_Date.<br>
</td></tr><tr><td>Filters<br></td><td>Provide additional filtering criteria as a JSON object to refine the object attachment. For e.g., {"Type":"File"})<br>
</td></tr><tr><td>Sort By<br></td><td>Select the sorting direction. You may use only one parameter either "Sort Ascending" or "Sort Descending" parameter.<br>
<strong>If you choose 'Sort Ascending'</strong><ul><li>Sort Ascending: Specify the comma-separated fields to be used for ascending sorting.</li></ul><strong>If you choose 'Sort Descending'</strong><ul><li>Sort Descending: Specify the comma-separated fields to be used for descending sorting.</li></ul></td></tr></td></tr>
<tr><td>Limit<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr><tr><td>Offset<br></td><td>Specifies how many records to omit before returning data. Should be paired with the "Limit" parameter for pagination.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Fields": [
            {
                "Name": "",
                "DataType": "",
                "Caption": ""
            }
        ],
        "Data": ""
    }
}
```

### operation: Get Attachment Content

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to retrieve attachment content from Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, or GUID)<br>
</td></tr><tr><td>Attachment ID<br></td><td>Specify the ID of the attachment to retrieve details from Alloy Navigator Express.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "responseObject": {
        "Data": "",
        "FileName": "",
        "Description": "",
        "Size": ""
    }
}
```

### operation: Download Attachment

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object identifier to download attachment from Alloy Navigator Express. Object identifier (e.g., T000027 for incidents, or GUID)<br>
</td></tr><tr><td>Attachment ID<br></td><td>Specify the ID of the attachment to retrieve details from Alloy Navigator Express.<br>
</td></tr><tr><td>Attachment Name<br></td><td>Specify the custom name of the attachment for the FortiSOAR attachment record.<br>
</td></tr><tr><td>Attachment Description<br></td><td>Specify the custom description of the attachment for the FortiSOAR attachment record.<br>
</td></tr><tr><td>Skip FortiSOAR Upload<br></td><td>Select this option to download the file without uploading it to FortiSOAR.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "message": "",
    "download": {
        "success": "",
        "file_name": "",
        "content_type": "",
        "size": "",
        "data": "",
        "message": ""
    },
    "fortisoar_upload": {
        "file_name": "",
        "content_type": "",
        "size": "",
        "fortisoar_file_iri": "",
        "fortisoar_attachment_iri": "",
        "fortisoar_attachment_id": "",
        "attachment_record": ""
    }
}
```

### operation: Add Attachments

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object ID for the Alloy Navigator record you want to attach a file to from FortiSOAR. Object identifier (e.g., T000027 for incidents, or GUID)<br>
</td></tr><tr><td>File or Attachment IRI<br></td><td>Specify the type of file that you want to submit to Alloy Navigator Express. The type can be an Attachment ID or a File IRI.<br>
<strong>If you choose 'Attachment IRI'</strong><ul><li>Attachment IRI: Specify the attachment IRI based on which you want to submit attachment to Alloy Navigator Express.</li></ul><strong>If you choose 'File IRI'</strong><ul><li>File IRI: Specify the file IRI based on which you want to submit attachment to Alloy Navigator Express.</li></ul></td></tr></tbody></table>

#### Output

The output contains a non-dictionary value.

### operation: Remove Attachment

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object ID of the Alloy Navigator record you want to remove the attachment from. Object identifier (e.g., T000027 for incidents, or GUID)<br>
</td></tr><tr><td>Attachment ID<br></td><td>Specify the attachment ID for the item you want to remove from Alloy Navigator Express.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "message": ""
}
```

### operation: Update Attachment Description

#### Input parameters

<table border=1><thead><tr><th>Parameter<br></th><th>Description<br></th></tr></thead><tbody><tr><td>Object Identifier (OID)<br></td><td>Specify the object ID of the Alloy Navigator record whose attachment description you want to update. Object identifier (e.g., T000027 for incidents, or GUID)<br>
</td></tr><tr><td>Attachment ID<br></td><td>Specify the attachment ID of the Alloy Navigator record whose attachment description you want to update.<br>
</td></tr><tr><td>Description<br></td><td>Specify the description of the Alloy Navigator record whose you want to update.<br>
</td></tr></tbody></table>

#### Output

The output contains the following populated JSON schema:

```
{
    "success": "",
    "errorCode": "",
    "errorText": "",
    "message": ""
}
```

## Included playbooks

The *`Sample - Alloy ITSM - 1.0.0`* playbook collection comes bundled with the Alloy ITSM connector. These playbooks
contain steps using which you can perform all supported actions. You can see bundled playbooks in the **Automation** > **Playbooks** section in FortiSOAR&trade; after importing the Alloy ITSM connector.

- Add Attachments
- Advanced Search for Classification Values
- Advanced Search for Object Activities
- Check Step Action Availability
- Create Object
- Download Attachment
- Get Attachment Content
- Get Classification Values
- Get Current User Profile
- Get Object Activities
- Get Object By ID
- Get Objects
- Get Objects Advanced Search
- List Object Attachments
- Remove Attachment
- Update Attachment Description
- Update Object

----
**Note**: 

If you are planning to use any of the sample playbooks in your environment, ensure that you clone those
playbooks and move them to a different collection, since the sample playbook collection gets deleted during connector
upgrade and delete.

----
