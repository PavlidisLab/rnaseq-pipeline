import luigi

from rnaseq_pipeline.platforms import IlluminaPlatform
from rnaseq_pipeline.sources.geo import match_geo_platform, DownloadGeoSampleMetadata, \
    DownloadGeoSeriesMetadata
from rnaseq_pipeline.utils import remove_task_output

def test_parse_illumina_platform():
    platform = match_geo_platform('GPL30172')
    assert isinstance(platform, IlluminaPlatform)
    assert platform.name == 'Illumina'
    assert platform.instrument == 'NextSeq 2000'

def test_download_geo_sample_metadata():
    t = DownloadGeoSampleMetadata('GSM6753395')
    remove_task_output(t)
    assert not t.complete()
    luigi.build([t], local_scheduler=True)
    assert t.complete()

def test_download_geo_series_metadata():
    t = DownloadGeoSeriesMetadata('GSE220114')
    remove_task_output(t)
    luigi.build([t], local_scheduler=True)
    assert t.complete()

# Offline tests: Entrez answers are faked, so these do not depend on NCBI or on NCBI_API_KEY.

import json
from os.path import dirname, join

import pytest

from rnaseq_pipeline.sources import geo
from rnaseq_pipeline.sources.geo import read_geo_sample_info, retrieve_geo_summary

test_data_dir = join(dirname(__file__), 'data')

class _FakeResponse:
    def __init__(self, status_code, payload, headers=None):
        self.status_code = status_code
        self.text = json.dumps(payload)
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload

def _fake_entrez(monkeypatch, responses):
    """Replace requests.get in the geo module; responses maps an Entrez endpoint to a response."""
    calls = []

    def get(url, params=None):
        endpoint = url.rsplit('/', 1)[1]
        calls.append((endpoint, dict(params)))
        response = responses[endpoint]
        # a list is consumed in order, one response per call
        return response.pop(0) if isinstance(response, list) else response

    monkeypatch.setattr(geo.requests, 'get', get)
    return calls

def _search(*uids):
    return _FakeResponse(200, {'esearchresult': {'idlist': list(uids)}})

def _summaries(*records):
    return _FakeResponse(200, {'result': {'uids': [r['uid'] for r in records], **{r['uid']: r for r in records}}})

def test_read_geo_sample_info():
    # a real esummary (db=gds) record for GSM9939224, saved 2026-10-27
    assert read_geo_sample_info(join(test_data_dir, 'GSM9939224.esummary.json')) == ('GPL24676', 'SRX34701233')

def test_read_geo_sample_info_without_sra(tmp_path):
    path = tmp_path / 'GSM1.json'
    path.write_text(json.dumps({'accession': 'GSM1', 'gpl': '570', 'extrelations': []}))
    assert read_geo_sample_info(path) is None

def test_retrieve_geo_summary_returns_the_record_for_the_accession(monkeypatch):
    monkeypatch.delenv('NCBI_API_KEY', raising=False)
    calls = _fake_entrez(monkeypatch, {
        'esearch.fcgi': _search('200342782', '309939224'),
        'esummary.fcgi': _summaries({'uid': '200342782', 'accession': 'GSE342782'},
                                    {'uid': '309939224', 'accession': 'GSM9939224', 'gpl': '24676'})})
    assert retrieve_geo_summary('GSM9939224', 'gsm')['gpl'] == '24676'
    assert calls[0][1]['term'] == 'GSM9939224[ACCN] AND gsm[ETYP]'
    assert all('api_key' not in params for _, params in calls)

def test_retrieve_geo_summary_uses_the_api_key_from_the_environment(monkeypatch):
    monkeypatch.setenv('NCBI_API_KEY', 'test-key')
    calls = _fake_entrez(monkeypatch, {
        'esearch.fcgi': _search('100024676'),
        'esummary.fcgi': _summaries({'uid': '100024676', 'accession': 'GPL24676',
                                     'title': 'Illumina NovaSeq 6000 (Homo sapiens)'})})
    assert retrieve_geo_summary('GPL24676', 'gpl')['title'] == 'Illumina NovaSeq 6000 (Homo sapiens)'
    assert all(params['api_key'] == 'test-key' for _, params in calls)

def test_a_rejected_api_key_is_reported_without_the_key(monkeypatch):
    monkeypatch.setenv('NCBI_API_KEY', 'secret-key')
    _fake_entrez(monkeypatch, {'esearch.fcgi': _FakeResponse(400, {
        'error': 'API key status invalid', 'api-key': 'secret-key', 'type': 'api-key', 'status': 'invalid'})})
    with pytest.raises(RuntimeError) as e:
        retrieve_geo_summary('GSM9939224', 'gsm')
    assert 'NCBI_API_KEY' in str(e.value)
    assert 'secret-key' not in str(e.value)

def test_an_error_in_a_200_response_is_raised(monkeypatch):
    monkeypatch.delenv('NCBI_API_KEY', raising=False)
    _fake_entrez(monkeypatch, {'esearch.fcgi': _FakeResponse(200, {'error': 'API rate limit exceeded'})})
    with pytest.raises(RuntimeError, match='rate limit'):
        retrieve_geo_summary('GSM9939224', 'gsm')

def test_an_unknown_accession_is_an_error(monkeypatch):
    monkeypatch.delenv('NCBI_API_KEY', raising=False)
    _fake_entrez(monkeypatch, {'esearch.fcgi': _search()})
    with pytest.raises(ValueError, match='No GEO record found for GSM0'):
        retrieve_geo_summary('GSM0', 'gsm')

def test_match_geo_platform_from_the_entrez_title(monkeypatch):
    monkeypatch.setattr(geo, 'retrieve_geo_platform_title', lambda gpl: 'Illumina NovaSeq 6000 (Homo sapiens)')
    platform = match_geo_platform('GPL24676')
    assert isinstance(platform, IlluminaPlatform) and platform.instrument == 'NovaSeq 6000'

_RATE_LIMITED = {'error': 'API rate limit exceeded', 'api-key': '137.82.176.27', 'count': '4', 'limit': '3'}

def test_a_rate_limited_request_is_retried(monkeypatch):
    monkeypatch.delenv('NCBI_API_KEY', raising=False)
    sleeps = []
    monkeypatch.setattr(geo.time, 'sleep', sleeps.append)
    calls = _fake_entrez(monkeypatch, {
        'esearch.fcgi': [_FakeResponse(429, _RATE_LIMITED), _FakeResponse(429, _RATE_LIMITED, {'Retry-After': '5'}),
                         _search('309939224')],
        'esummary.fcgi': _summaries({'uid': '309939224', 'accession': 'GSM9939224', 'gpl': '24676'})})
    assert retrieve_geo_summary('GSM9939224', 'gsm')['gpl'] == '24676'
    assert sleeps == [1, 5.0], 'doubling delay, and Retry-After wins when NCBI sends it'
    assert [endpoint for endpoint, _ in calls] == ['esearch.fcgi'] * 3 + ['esummary.fcgi']

def test_retries_are_bounded_and_the_ip_in_a_keyless_error_is_not_called_a_bad_key(monkeypatch):
    monkeypatch.delenv('NCBI_API_KEY', raising=False)
    sleeps = []
    monkeypatch.setattr(geo.time, 'sleep', sleeps.append)
    _fake_entrez(monkeypatch, {'esearch.fcgi': _FakeResponse(429, _RATE_LIMITED)})
    with pytest.raises(RuntimeError) as e:
        retrieve_geo_summary('GSM9939224', 'gsm')
    assert len(sleeps) == geo.EUTILS_RATE_LIMIT_RETRIES
    assert 'HTTP 429' in str(e.value) and 'rejected the API key' not in str(e.value)
