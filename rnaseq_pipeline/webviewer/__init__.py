from os.path import basename

import luigi
from flask import Flask, send_file, render_template, url_for, request, abort
import pandas as pd

from rnaseq_pipeline.config import rnaseq_pipeline
from rnaseq_pipeline.tasks import GenerateReportForExperiment, CountExperiment, ExtractGeoSeriesBatchInfo, SubmitExperimentDataToGemma, SubmitExperimentBatchInfoToGemma
from rnaseq_pipeline.utils import GemmaTask

app = Flask('rnaseq_pipeline.webviewer')

cfg = rnaseq_pipeline()

references = ['hg38_ncbi', 'mm10_ncbi', 'm6_ncbi']

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html', e=e), 400

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', e=e), 404

@app.route('/experiment/<experiment_id>')
def experiment_summary(experiment_id):
    try:
        submit_data_task = SubmitExperimentDataToGemma(experiment_id)
    except:
        abort(404, f'Experiment {experiment_id} is not found in Gemma database.')

    submit_batch_info_task = SubmitExperimentBatchInfoToGemma(experiment_id)
    ebi_task = submit_batch_info_task.requires()
    if ebi_task.complete():
        batch_info = pd.read_csv(ebi_task.output().path, sep='\t', names=['geo_sample_id', 'sra_run_id', 'geo_platform_id', 'sra_experiment_url', 'fastq_header'])
    else:
        batch_info = None

    return render_template('experiment-summary.html',
            experiment_id=experiment_id, batch_info=batch_info,
            submit_data_task=submit_data_task,
            submit_batch_info_task=submit_batch_info_task)

@app.route('/experiment/<experiment_id>/batch-info')
def experiment_batch_info(experiment_id):
    submit_batch_info_task = SubmitExperimentBatchInfoToGemma(experiment_id)
    ebi_task = submit_batch_info_task.requires()
    batch_info_path = ebi_task.output().path
    if not ebi_task.complete():
        abort(404, f'No batch info available for {experiment_id}.')
    return send_file(batch_info_path, as_attachment=True, attachment_filename=basename(batch_info_path))

@app.route('/experiment/<experiment_id>/quantifications/<mode>')
@app.route('/experiment/<experiment_id>/by-reference-id/<reference_id>/quantifications/<mode>')
def experiment_quantifications(experiment_id, mode, reference_id=None):
    if reference_id is None:
        gemma_task = GemmaTask(experiment_id)
        reference_id = gemma_task.reference_id
    try:
        mode_ix = ['counts', 'fpkm'].index(mode)
    except ValueError:
        abort(400, f'Unknown mode {mode} for quantifications, try either counts or fpkm.')
    count_experiment_task = CountExperiment(experiment_id, reference_id=reference_id)
    if not count_experiment_task.complete():
        abort(404, f'No quantifications available for {experiment_id} in {reference_id}.')
    file_path = count_experiment_task.output()[mode_ix].path
    return send_file(file_path, as_attachment=True, attachment_filename=basename(file_path))

@app.route('/experiment/<experiment_id>/report')
@app.route('/experiment/<experiment_id>/by-reference-id/<reference_id>/report')
def experiment_report(experiment_id, reference_id=None):
    if reference_id is None:
        gemma_task = GemmaTask(experiment_id)
        reference_id = gemma_task.reference_id
    generate_report_task = GenerateReportForExperiment(experiment_id, reference_id=reference_id)
    if not generate_report_task.complete():
        abort(404, f'No report available for {experiment_id} in {reference_id}.')
    return send_file(generate_report_task.output().path)

if __name__ == '__main__':
    app.run(debug=True)
