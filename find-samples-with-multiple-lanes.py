import tarfile
import tempfile
from io import StringIO
from urllib.parse import urlparse, parse_qs

import pandas as pd
import requests
from tqdm import tqdm

from rnaseq_pipeline.miniml_utils import collect_geo_samples_info

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}

def retrieve_geo_series_miniml_from_ftp(gse):
    res = requests.get(f'https://ftp.ncbi.nlm.nih.gov/geo/series/{gse[:-3]}nnn/{gse}/miniml/{gse}_family.xml.tgz',
                       stream=True)
    res.raise_for_status()
    # we need to use a temporary file because Response.raw does not allow seeking
    with tempfile.TemporaryFile() as tmp:
        for chunk in res.iter_content(chunk_size=1024):
            tmp.write(chunk)
        tmp.seek(0)
        with tarfile.open(fileobj=tmp, mode='r:gz') as fin:
            reader = fin.extractfile(f'{gse}_family.xml')
            return reader.read().decode('utf-8')

def retrieve_geo_series_miniml_from_geo_query(gse):
    res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=gse, form='xml', targ='gsm'))
    res.raise_for_status()
    return res.text

def fetch_sra_metadata(gse):
    try:
        miniml = retrieve_geo_series_miniml_from_ftp(gse)
    except Exception as e:
        print(
            f'Failed to retrieve MINiML metadata for {gse} from NCBI FTP server will attempt to use GEO directly.',
            e)
        try:
            miniml = retrieve_geo_series_miniml_from_geo_query(gse)
        except Exception as e:
            print(f'Failed to retrieve MINiML metadata for {gse} from GEO query.', e)
            return []
    try:
        meta = collect_geo_samples_info(StringIO(miniml))
    except Exception as e:
        print('Failed to parse MINiML from input: ' + miniml[:100], e)
        return []
    results = []
    for gsm in meta:
        platform, srx_url = meta[gsm]
        srx = parse_qs(urlparse(srx_url).query)['term'][0]
        results.append((gse, gsm, srx))
    return results

with open('geo-sample-to-sra-experiment.tsv', 'wt') as f:
    print('geo_series', 'geo_sample', 'sra_experiment', file=f, sep='\t', flush=True)
    df = pd.read_table('gemma-rnaseq-datasets.tsv')
    batch = []
    for gse in tqdm(df.geo_accession):
        samples = fetch_sra_metadata(gse)
        for sample in samples:
            print(*sample, file=f, sep='\t', flush=True)

# def fetch_runinfo(srx_ids):
#     # fetch the SRX metadata
#     return pd.read_csv(StringIO(retrieve_runinfo(srx_ids)))
#
# def print_results(samples):
#     srx_ids = [s[2] for s in samples]
#     try:
#         results = fetch_runinfo(srx_ids)
#     except Exception as e:
#         print('Failed to retrieve runinfo for the following SRX IDs:', srx_ids, e)
#         return
#     for sample in samples:
#         runs = results[results['Experiment'] == sample[2]]['Run']
#         r = sample + ('|'.join(runs), len(runs))
#         print(*r, sep='\t', flush=True)
#
# BATCH_SIZE = 100
