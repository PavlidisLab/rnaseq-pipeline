from os.path import join
from glob import glob
import luigi
from flask import Flask, send_file

from rnaseq_pipeline.config import core

app = Flask('rnaseq_pipeline.viewer')
cfg = core()

@app.route('/report/<experiment_id>')
def multiqc_report(experiment_id):
    matches = glob(join(cfg.OUTPUT_DIR, 'report', '*_ncbi', experiment_id, 'multiqc_report.html'))
    if not matches:
        return f'No such report {experiment_id}.', 404
    return send_file(matches[0])

if __name__ == '__main__':
    app.run(debug=True)
