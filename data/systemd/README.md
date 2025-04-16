This directory contains systemctl unit and timers to launch the RNA-Seq
pipeline and its webviewer.

To edit the configuration, issue: `systemctl edit rnaseq-pipeline-worker@.service` and `systemctl edit rnaseq-pipeline-viewer.service`
to add the following environment variables:

```
[Service]
WorkingDirectory=/location/of/the/pipeline/configuration
Environment="CONDA_ENV=/path/to/conda/env"
Environment="GEMMA_USERNAME={username}"
Environment="GEMMA_PASSWORD={password}"
```

# Launch workers

We run two workers, one is generally idle and awaits new datasets to be
processed in a collaborative spreadsheet by our curators, the other is
generally busy. Those are configured to restart after 20 minutes after exiting.

```
systemctl start rnaseq-pipeline-worker@1.service rnaseq-pipeline-worker@2.service
```

# Launch the viewer

```
systemctl start rnaseq-pipeline-viewer.service
```

# Enable the cleanup unit

Edit the configuration to set the working directory where the cleanup script
can be resolved.

```
[Service]
WorkingDirectory=/location/of/the/pipeline/configuration
```

```
systemctl start rnaseq-pipeline-cleanup.timer
```
