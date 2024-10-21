# **Comprehensive Implementation Guide: Integrating SWAIG with Zendesk Support API and Support PIN Authentication**

---

## **Table of Contents**

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Step 1: Set Up Zendesk API Access](#step-1-set-up-zendesk-api-access)
   - 1.1 [Create an API Token](#11-create-an-api-token)
   - 1.2 [Create Custom User Fields (Support PIN)](#12-create-custom-user-fields-support-pin)
5. [Step 2: Set Up SignalWire AI Gateway (SWAIG)](#step-2-set-up-signalwire-ai-gateway-swaig)
6. [Step 3: Define SWAIG Functions Mapping to Zendesk API](#step-3-define-swaig-functions-mapping-to-zendesk-api)
   - 3.1 [Function Definitions with SignalWire AI Gateway (SWAIG)](#31-function-definitions-with-openai-tool-json)
   - 3.2 [Full Function Implementations](#32-full-function-implementations)
7. [Step 4: Implement Support PIN Authentication](#step-4-implement-support-pin-authentication)
   - 4.1 [Generate and Assign Support PINs](#41-generate-and-assign-support-pins)
   - 4.2 [Store PINs in Zendesk](#42-store-pins-in-zendesk)
   - 4.3 [Create SWAIG Function for PIN Verification](#43-create-swaig-function-for-pin-verification)
8. [Step 5: Integrate PIN Authentication with SWAIG Functions](#step-5-integrate-pin-authentication-with-swaig-functions)
9. [Step 6: Complete Argument Mappings](#step-6-complete-argument-mappings)
10. [Step 7: Testing and Error Handling](#step-7-testing-and-error-handling)
11. [Step 8: Security Considerations](#step-8-security-considerations)
12. [Conclusion](#conclusion)
13. [Appendix: Code Examples](#appendix-code-examples)
    - A. [SignalWire AI Gateway (SWAIG) Definitions](#a-openai-tool-json-definitions)
    - B. [Complete Function Code Implementations](#b-complete-function-code-implementations)

---

## **Introduction**

This guide provides a comprehensive walkthrough for implementing an AI Agent that uses the SignalWire AI Gateway (SWAIG) to interact with the Zendesk Support API. The AI Agent will be capable of creating, updating, and closing tickets, adding comments, and authenticating users via phone using a support PIN.

---

## **Architecture Overview**

- **AI Agent**: Interfaces with users via phone calls.
- **SignalWire AI Gateway (SWAIG)**: Acts as a middleware, handling AI Agent functions and mapping them to Zendesk API endpoints.
- **Zendesk Support API**: Manages support tickets and user data.
- **Support PIN Authentication**: Verifies users over the phone before allowing ticket operations.

---

## **Prerequisites**

- A **Zendesk** account with admin access.
- Access to **SignalWire AI Gateway (SWAIG)**.
- Programming knowledge in **Python** (or your preferred language).
- **Python Libraries**:
  - `Flask` for creating the web server.
  - `requests` for making HTTP requests.
  - `python-dotenv` for loading environment variables from a `.env` file.
  - `json` for handling JSON data.
  - `secrets` for generating secure random numbers (used for PIN generation).
  - `os` for accessing environment variables.
  - `requests.auth` for handling HTTP Basic Authentication.

---

## **Step 1: Set Up Zendesk API Access**

### **1.1 Create an API Token**

1. **Log in to Zendesk**.
2. Navigate to **Admin Center** > **Apps and integrations** > **Zendesk API** > **Zendesk API Settings**.
3. Enable **Token Access**.
4. Click **Add API Token**.
5. Enter a description and click **Create**.
6. Copy the generated token and store it securely.

### **1.2 Create Custom User Fields (Support PIN)**

1. Navigate to **Admin Center** > **People** > **Configuration** > **User Fields**.
2. Click **Add Field**.
3. Configure the field:
   - **Type**: **Text** (or **Numeric** if the PIN is digits only).
   - **Title**: `Support PIN`.
   - **Key**: `support_pin`.
4. Save the new custom field.

---

## **Step 2: Set Up SignalWire AI Gateway (SWAIG)**

1. **Install SWAIG** according to the official documentation.
2. **Configure SWAIG** to handle function calls and map them to external APIs.
3. **Set up Environment Variables** for sensitive data:
   - `ZENDESK_SUBDOMAIN`
   - `ZENDESK_EMAIL`
   - `ZENDESK_API_TOKEN`

---

## **Step 3: Define SWAIG Functions Mapping to Zendesk API**

### **3.1 Function Definitions with SignalWire AI Gateway (SWAIG)**

For each function, we provide:

- **Function Name**
- **Description**
- **SignalWire AI Gateway (SWAIG)**: Defines the function for SWAIG.
- **Zendesk API Endpoint**

#### **Function 1: create_ticket**

- **Description**: Creates a new support ticket in Zendesk.
- **Zendesk API Endpoint**: `POST /api/v2/tickets.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "create_ticket",
  "description": "Creates a new support ticket in Zendesk.",
  "parameters": {
    "type": "object",
    "properties": {
      "subject": {
        "type": "string",
        "description": "The subject or title of the ticket."
      },
      "comment_body": {
        "type": "string",
        "description": "The initial comment or description of the ticket."
      },
      "requester_name": {
        "type": "string",
        "description": "Name of the requester."
      },
      "requester_email": {
        "type": "string",
        "description": "Email of the requester."
      },
      "priority": {
        "type": "string",
        "description": "Priority level of the ticket.",
        "enum": ["low", "normal", "high", "urgent"],
        "nullable": true
      }
    },
    "required": ["subject", "comment_body", "requester_name", "requester_email"]
  }
}
```

#### **Function 2: update_ticket**

- **Description**: Updates an existing support ticket in Zendesk.
- **Zendesk API Endpoint**: `PUT /api/v2/tickets/{ticket_id}.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "update_ticket",
  "description": "Updates an existing support ticket in Zendesk.",
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {
        "type": "integer",
        "description": "The ID of the ticket to update."
      },
      "status": {
        "type": "string",
        "description": "The status to update the ticket to.",
        "enum": ["new", "open", "pending", "hold", "solved", "closed"],
        "nullable": true
      },
      "priority": {
        "type": "string",
        "description": "Priority level of the ticket.",
        "enum": ["low", "normal", "high", "urgent"],
        "nullable": true
      },
      "comment_body": {
        "type": "string",
        "description": "A comment to add to the ticket.",
        "nullable": true
      },
      "public": {
        "type": "boolean",
        "description": "Whether the comment is public (visible to the requester).",
        "default": true,
        "nullable": true
      }
    },
    "required": ["ticket_id"]
  }
}
```

#### **Function 3: close_ticket**

- **Description**: Closes a support ticket in Zendesk by updating its status to "closed".
- **Zendesk API Endpoint**: `PUT /api/v2/tickets/{ticket_id}.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "close_ticket",
  "description": "Closes a support ticket in Zendesk by setting its status to 'closed'.",
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {
        "type": "integer",
        "description": "The ID of the ticket to close."
      }
    },
    "required": ["ticket_id"]
  }
}
```

#### **Function 4: add_comment**

- **Description**: Adds a comment to an existing support ticket in Zendesk.
- **Zendesk API Endpoint**: `PUT /api/v2/tickets/{ticket_id}.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "add_comment",
  "description": "Adds a comment to an existing support ticket in Zendesk.",
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {
        "type": "integer",
        "description": "The ID of the ticket to add a comment to."
      },
      "comment_body": {
        "type": "string",
        "description": "Content of the comment."
      },
      "public": {
        "type": "boolean",
        "description": "Whether the comment is public (visible to the requester).",
        "default": true,
        "nullable": true
      }
    },
    "required": ["ticket_id", "comment_body"]
  }
}
```

#### **Function 5: get_ticket**

- **Description**: Retrieves information about a specific ticket in Zendesk.
- **Zendesk API Endpoint**: `GET /api/v2/tickets/{ticket_id}.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "get_ticket",
  "description": "Retrieves information about a specific ticket in Zendesk.",
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {
        "type": "integer",
        "description": "The ID of the ticket to retrieve."
      }
    },
    "required": ["ticket_id"]
  }
}
```

#### **Function 6: verify_support_pin**

- **Description**: Verifies the caller's support PIN against the stored PIN in Zendesk.
- **Zendesk API Endpoint**: `GET /api/v2/search.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "verify_support_pin",
  "description": "Verifies the caller's support PIN against the stored PIN in Zendesk.",
  "parameters": {
    "type": "object",
    "properties": {
      "caller_phone_number": {
        "type": "string",
        "description": "The caller's phone number."
      },
      "entered_pin": {
        "type": "integer",
        "description": "The support PIN entered by the caller."
      }
    },
    "required": ["caller_phone_number", "entered_pin"]
  }
}
```

#### **Function 7: get_current_user_tickets**

- **Description**: Retrieves ticket numbers for the authenticated user.
- **Zendesk API Endpoint**: `GET /api/v2/users/{user_id}/tickets/requested.json`

**SignalWire AI Gateway (SWAIG) Definition**:

```json
{
  "name": "get_current_user_tickets",
  "description": "Retrieves ticket numbers for the authenticated user.",
  "parameters": {
    "type": "object",
    "properties": {
      "caller_phone_number": {
        "type": "string",
        "description": "The caller's phone number."
      },
      "status": {
        "type": "string",
        "description": "Filter tickets by status.",
        "enum": ["new", "open", "pending", "hold", "solved", "closed"],
        "nullable": true
      },
      "priority": {
        "type": "string",
        "description": "Filter tickets by priority.",
        "enum": ["low", "normal", "high", "urgent"],
        "nullable": true
      }
    },
    "required": ["caller_phone_number"]
  }
}
```

### **3.2 Full Function Implementations**

Provide the full code implementations for each function.

**Note**: Replace placeholders like `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, and `ZENDESK_API_TOKEN` with your actual Zendesk subdomain, email, and API token, respectively.

#### **Function: create_ticket**

```python
import os
import requests
from requests.auth import HTTPBasicAuth

# Retrieve environment variables
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')
ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL')
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN')

def create_ticket(
    subject,
    comment_body,
    requester_name=None,
    requester_email=None,
    priority=None,
):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json'
    ticket_data = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": comment_body
            }
        }
    }
    if requester_name or requester_email:
        ticket_data["ticket"]["requester"] = {}
        if requester_name:
            ticket_data["ticket"]["requester"]["name"] = requester_name
        if requester_email:
            ticket_data["ticket"]["requester"]["email"] = requester_email
    if priority:
        ticket_data["ticket"]["priority"] = priority

    response = requests.post(
        url,
        json=ticket_data,
        auth=HTTPBasicAuth(f'{ZENDESK_EMAIL}/token', ZENDESK_API_TOKEN)
    )
    return response.json()
```

#### **Function: update_ticket**

```python
def update_ticket(
    ticket_id,
    status=None,
    priority=None,
    comment_body=None,
    public=True,
):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json'
    ticket_data = {"ticket": {}}
    if status:
        ticket_data["ticket"]["status"] = status
    if priority:
        ticket_data["ticket"]["priority"] = priority
    if comment_body:
        ticket_data["ticket"]["comment"] = {
            "body": comment_body,
            "public": public
        }

    response = requests.put(
        url,
        json=ticket_data,
        auth=HTTPBasicAuth(f'{ZENDESK_EMAIL}/token', ZENDESK_API_TOKEN)
    )
    return response.json()
```

#### **Function: close_ticket**

```python
def close_ticket(ticket_id, comment_body=None, public=True):
    return update_ticket(
        ticket_id,
        status='closed',
        comment_body=comment_body,
        public=public
    )
```

#### **Function: add_comment**

```python
def add_comment(ticket_id, comment_body, public=True):
    return update_ticket(
        ticket_id,
        comment_body=comment_body,
        public=public
    )
```

#### **Function: get_ticket**

```python
def get_ticket(ticket_id):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json'
    response = requests.get(
        url,
        auth=HTTPBasicAuth(f'{ZENDESK_EMAIL}/token', ZENDESK_API_TOKEN)
    )
    return response.json()
```

#### **Function: verify_support_pin**

```python
def verify_support_pin(caller_phone_number, entered_pin):
    user = find_user_by_phone(caller_phone_number)
    if user:
        stored_pin = user.get('user_fields', {}).get('support_pin')
        if stored_pin == entered_pin:
            return True
    return False

def find_user_by_phone(caller_phone_number):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/search.json'
    params = {
        'query': f'type:user phone:"{caller_phone_number}"'
    }
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(f'{ZENDESK_EMAIL}/token', ZENDESK_API_TOKEN)
    )
    results = response.json().get('results', [])
    return results[0] if results else None
```

#### **Function: get_current_user_tickets**

```python
def get_current_user_tickets(caller_phone_number, status=None, priority=None):
    user = find_user_by_phone(caller_phone_number)
    if user:
        user_id = user['id']
        tickets = list_user_tickets(user_id, status=status, priority=priority)
        if tickets:
            ticket_numbers = [ticket['id'] for ticket in tickets.get('tickets', [])]
            return {
                'ticket_numbers': ticket_numbers,
                'tickets': tickets.get('tickets', [])
            }
        else:
            return {
                'message': "No tickets found for your account."
            }
    else:
        return {
            'message': "User not found."
        }
```

---

## **Step 4: Implement Support PIN Authentication**

### **4.1 Generate and Assign Support PINs**

Use a secure method to generate unique PINs for users.

**Example in Python**:

```python
import secrets

def generate_support_pin(length=6):
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
```

Assign the PIN to the user during registration or onboarding.

### **4.2 Store PINs in Zendesk**

Update the user's profile with the support PIN using the Zendesk API.

**API Endpoint**: `PUT /api/v2/users/{user_id}.json`

**Python Function**:

```python
def update_user_support_pin(user_id, support_pin):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/{user_id}.json'
    data = {
        "user": {
            "user_fields": {
                "support_pin": support_pin
            }
        }
    }
    response = requests.put(
        url,
        json=data,
        auth=HTTPBasicAuth(f'{ZENDESK_EMAIL}/token', ZENDESK_API_TOKEN)
    )
    return response.json()
```

### **4.3 Create SWAIG Function for PIN Verification**

As provided in Section 3.2, the `verify_support_pin` function and its code are fully defined.

---

## **Step 5: Integrate PIN Authentication with SWAIG Functions**

Modify SWAIG to incorporate PIN verification before executing any ticket operations.

**Example Workflow**:

1. **User Calls Support**.
2. **AI Agent Prompts for PIN**.
3. **User Enters PIN**.
4. **SWAIG Calls `verify_support_pin`**.
   - If verification succeeds, proceed.
   - If verification fails, handle accordingly.
5. **Execute Requested SWAIG Function**.

---

## **Step 6: Complete Argument Mappings**

Ensure all SWAIG function arguments map correctly to Zendesk API parameters.

### **Example: `create_ticket` Argument Mapping**

- **SWAIG Function Arguments**:
  - `subject`
  - `comment_body`
  - `requester_name`
  - `requester_email`
  - `priority`

- **Zendesk API Payload**:

  ```json
  {
    "ticket": {
      "subject": "subject",
      "comment": {
        "body": "comment_body"
      },
      "requester": {
        "name": "requester_name",
        "email": "requester_email"
      },
      "priority": "priority"
    }
  }
  ```

### **Example: `update_ticket` Argument Mapping**

- **SWAIG Function Arguments**:
  - `ticket_id`
  - `status`
  - `priority`
  - `comment_body`
  - `public`

- **Zendesk API Payload**:

  ```json
  {
    "ticket": {
      "status": "status",
      "priority": "priority",
      "comment": {
        "body": "comment_body",
        "public": "public"
      }
    }
  }
  ```

### **Example: `close_ticket` Argument Mapping**

- **SWAIG Function Arguments**:
  - `ticket_id`

- **Zendesk API Payload**:

  ```json
  {
    "ticket": {
      "status": "closed"
    }
  }
  ```

### **Example: `add_comment` Argument Mapping**

- **SWAIG Function Arguments**:
  - `ticket_id`
  - `comment_body`
  - `public`

- **Zendesk API Payload**:

  ```json
  {
    "ticket": {
      "comment": {
        "body": "comment_body",
        "public": "public"
      }
    }
  }
  ```

### **Example: `get_ticket` Argument Mapping**

- **SWAIG Function Arguments**:
  - `ticket_id`

- **Zendesk API Endpoint**: `GET /api/v2/tickets/{ticket_id}.json`

### **Example: `verify_support_pin` Argument Mapping**

- **SWAIG Function Arguments**:
  - `caller_phone_number`
  - `entered_pin`

- **Zendesk API Endpoint**: `GET /api/v2/search.json`

### **Example: `get_current_user_tickets` Argument Mapping**

- **SWAIG Function Arguments**:
  - `caller_phone_number`
  - `status`
  - `priority`

- **Zendesk API Endpoint**: `GET /api/v2/users/{user_id}/tickets/requested.json`

---

## **Step 7: Testing and Error Handling**

### **7.1 Testing**

- **Unit Tests**: Test individual functions with mock data.
- **Integration Tests**: Simulate end-to-end workflows.
- **User Acceptance Testing (UAT)**: Have actual users test the system.

### **7.2 Error Handling**

- **HTTP Errors**: Check response status codes.
- **Validation Errors**: Ensure all required fields are provided.
- **Authentication Failures**: Handle incorrect PIN entries gracefully.

---

## **Step 8: Security Considerations**

- **Store Credentials Securely**: Use environment variables or a secrets manager.
- **Encrypt Sensitive Data**: Consider encrypting support PINs.
- **Compliance**: Adhere to GDPR and other data protection regulations.
- **Logging**: Avoid logging sensitive information.

---

## **Conclusion**

By following this guide, you can implement an AI Agent that interacts with Zendesk through SWAIG, providing users with the ability to manage support tickets over the phone securely. The integration of support PIN authentication adds an extra layer of security, ensuring that only authorized users can access and modify their tickets.

---

## **Appendix: Code Examples**

### **A. SignalWire AI Gateway (SWAIG) Definitions**

[Provided in Section 3.1]

### **B. Complete Function Code Implementations**

[Provided in Section 3.2]

---

**Note**: Replace placeholders like `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, and `ZENDESK_API_TOKEN` with your actual Zendesk subdomain, email, and API token, respectively.

---




