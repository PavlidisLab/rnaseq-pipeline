from rnaseq_pipeline.sources.arrayexpress import DownloadArrayExpressExperiment

def test():
    task = DownloadArrayExpressExperiment(experiment_id='E-MTAB-13839')
    for download_sample_task in task.run():
        print(download_sample_task)