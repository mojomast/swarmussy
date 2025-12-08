#!/usr/bin/env python3
"""
Grid API QA Harness
This script:
- Gracefully skips if GRID_API_BASE_URL is not configured
- Performs a minimal set of integration checks against the Grid API
  - health check
  - list flows (tries common endpoints)
  - error state validation (unauthenticated access)
  - optional asset lifecycle (requires GRID_API_TOKEN)
- Writes a JSON report to shared/qa_harness/grid_api_test_report.json

Run: GRID_API_BASE_URL=https://example.com GRID_API_TOKEN=secret python3 grid_api_tests.py
"""
import os
import json
import time
import random
import urllib.request
import urllib.error
from urllib.parse import urljoin

REPORT_PATH = os.path.join(os.path.dirname(__file__), 'grid_api_test_report.json')


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {}, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except urllib.error.URLError as e:
        return None, str(e)


def http_post(url, payload, headers=None):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers or {}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except urllib.error.URLError as e:
        return None, str(e)


def ensure_dir(path):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def main():
    base = os.environ.get('GRID_API_BASE_URL')
    token = os.environ.get('GRID_API_TOKEN')

    if not base:
        result = {
            'grid_api_base': None,
            'status': 'skipped',
            'reason': 'GRID_API_BASE_URL not configured; tests skipped gracefully.'
        }
        ensure_dir(REPORT_PATH)
        with open(REPORT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result, indent=2))
        return 0

    base = base.rstrip('/')
    report = {
        'grid_api_base': base,
        'status': 'in_progress',
        'start_time': int(time.time()),
        'steps': {}
    }

    # Health check
    health_url = urljoin(base if base.endswith('/') else base + '/', 'health')
    st, body = http_get(health_url)
    report['steps']['health'] = {
        'url': health_url,
        'status': st,
        'body': body
    }

    # Try common flows list endpoints
    candidate_endpoints = [
        urljoin(base if base.endswith('/') else base + '/', 'grid/flows'),
        urljoin(base if base.endswith('/') else base + '/', 'flows'),
        urljoin(base if base.endswith('/') else base + '/', 'grid/flow'),
    ]

    flows_status = None
    flows_body = ''
    for ep in candidate_endpoints:
        st, body = http_get(ep, headers=None)
        report['steps']['flow_list_endpoint'] = {
            'url': ep,
            'status': st,
            'body_snippet': body[:200] if body else ''
        }
        if st == 200:
            flows_status = 200
            flows_body = body
            break
    if flows_status != 200:
        report['steps']['flow_list'] = {
            'status': 'missing_or_not_200',
            'endpoints_tried': candidate_endpoints
        }
    else:
        report['steps']['flow_list'] = {
            'status': 200,
            'endpoints_tried': candidate_endpoints,
            'body_snippet': flows_body[:200] if flows_body else ''
        }

    # Basic error-state validation: unauthenticated access should be blocked for a protected endpoint
    unauth_ep = candidate_endpoints[0]
    st, _ = http_get(unauth_ep, headers={})  # explicitly no auth header
    report['steps']['unauth_access'] = {
        'url': unauth_ep,
        'status': st
    }

    # Asset lifecycle (optional, requires token)
    asset_report = {'token_required': False, 'assets': {} }
    if token:
        asset_report['token_required'] = True
        asset_headers = {'Authorization': f'Bearer {token}'}
        assets_url = urljoin(base if base.endswith('/') else base + '/', 'assets')
        ts = int(time.time())
        payload = {
            'name': f'qa-tester-{ts}',
            'type': 'qa',
            'description': 'Automated QA harness asset lifecycle test'
        }
        st, body = http_post(assets_url, payload, headers=asset_headers)
        asset_id = None
        if st in (200, 201, 202):
            try:
                asset_id = json.loads(body).get('id') if body else None
            except Exception:
                asset_id = None
        asset_report['assets']['create'] = {
            'url': assets_url,
            'status': st,
            'id': asset_id
        }
        if asset_id:
            # Get asset
            get_url = urljoin(assets_url if assets_url.endswith('/') else assets_url + '/', str(asset_id))
            st2, body2 = http_get(get_url, headers=asset_headers)
            asset_report['assets']['get'] = {
                'url': get_url,
                'status': st2,
                'body_snippet': (body2[:200] if body2 else '')
            }
            # Delete asset
            delete_req = urllib.request.Request(get_url, method='DELETE', headers=asset_headers)
            try:
                with urllib.request.urlopen(delete_req, timeout=10) as resp:
                    asset_report['assets']['delete'] = {
                        'url': get_url,
                        'status': resp.status
                    }
            except urllib.error.HTTPError as e:
                asset_report['assets']['delete'] = {
                    'url': get_url,
                    'status': e.code,
                    'body': e.read().decode('utf-8')
                }
            except urllib.error.URLError as e:
                asset_report['assets']['delete'] = {
                    'url': get_url,
                    'status': None,
                    'error': str(e)
                }
        else:
            asset_report['assets']['create'] = {
                'status': st,
                'body': body
            }

    report['steps']['asset_lifecycle'] = asset_report

    report['status'] = 'done'
    report['end_time'] = int(time.time())

    ensure_dir(REPORT_PATH)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        # Ensure report exists even on failure
        report = {
            'grid_api_base': os.environ.get('GRID_API_BASE_URL'),
            'status': 'error',
            'error': str(e)
        }
        ensure_dir(REPORT_PATH)
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        raise
