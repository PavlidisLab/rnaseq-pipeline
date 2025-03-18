complete -c luigi-wrapper -e
complete -c luigi-wrapper -f
complete -c luigi-wrapper -f -l TestNotificationsTask-raise-in-complete -d 'If true, fail in complete() instead of run()'
complete -c luigi-wrapper -f -l email-force-send -d 'Send e-mail even from a tty'
complete -c luigi-wrapper -f -l email-format -r -d 'Format type for sent e-mails Choices: {html, none, plain}'
complete -c luigi-wrapper -f -l email-method -r -d 'Method for sending e-mail Choices: {ses, sns, sendgrid, smtp}'
complete -c luigi-wrapper -f -l email-prefix -r -d 'Prefix for subject lines of all e-mails'
complete -c luigi-wrapper -f -l email-receiver -r -d 'Address to send error e-mails to'
complete -c luigi-wrapper -f -l email-traceback-max-length -r -d 'Max length for error traceback'
complete -c luigi-wrapper -f -l email-sender -r -d 'Address to send e-mails from'
complete -c luigi-wrapper -f -l smtp-host -r -d 'Hostname of smtp server'
complete -c luigi-wrapper -f -l smtp-local-hostname -r -d 'If specified, local_hostname is used as the FQDN of the local host in the HELO/EHLO command'
complete -c luigi-wrapper -f -l smtp-no-tls -d 'Do not use TLS in SMTP connections'
complete -c luigi-wrapper -f -l smtp-password -r -d 'Password for the SMTP server login'
complete -c luigi-wrapper -f -l smtp-port -r -d 'Port number for smtp server'
complete -c luigi-wrapper -f -l smtp-ssl -d 'Use SSL for the SMTP connection.'
complete -c luigi-wrapper -f -l smtp-timeout -r -d 'Number of seconds before timing out the smtp connection'
complete -c luigi-wrapper -f -l smtp-username -r -d 'Username used to log in to the SMTP host'
complete -c luigi-wrapper -f -l sendgrid-apikey -r -d 'API key for SendGrid login'
complete -c luigi-wrapper -f -l batch-email-email-interval -r -d 'Number of minutes between e-mail sends (default: 60)'
complete -c luigi-wrapper -f -l batch-email-batch-mode -r -d 'Method used for batching failures in e-mail. If "family" all failures for tasks with the same family will be batched. If "unbatched_params", all failures for tasks with the same family and non-batched parameters will be batched. If "all", tasks will only be batched if they have identical names. Choices: {family, all, unbatched_params}'
complete -c luigi-wrapper -f -l batch-email-error-lines -r -d 'Number of lines to show from each error message. 0 means show all'
complete -c luigi-wrapper -f -l batch-email-error-messages -r -d 'Number of error messages to show for each group'
complete -c luigi-wrapper -f -l batch-email-group-by-error-messages -d 'Group items with the same error messages together'
complete -c luigi-wrapper -f -l scheduler-retry-delay -r
complete -c luigi-wrapper -f -l scheduler-remove-delay -r
complete -c luigi-wrapper -f -l scheduler-worker-disconnect-delay -r
complete -c luigi-wrapper -f -l scheduler-state-path -r
complete -c luigi-wrapper -f -l scheduler-batch-emails -d 'Send e-mails in batches rather than immediately'
complete -c luigi-wrapper -f -l scheduler-disable-window -r
complete -c luigi-wrapper -f -l scheduler-retry-count -r
complete -c luigi-wrapper -f -l scheduler-disable-hard-timeout -r
complete -c luigi-wrapper -f -l scheduler-disable-persist -r
complete -c luigi-wrapper -f -l scheduler-max-shown-tasks -r
complete -c luigi-wrapper -f -l scheduler-max-graph-nodes -r
complete -c luigi-wrapper -f -l scheduler-record-task-history
complete -c luigi-wrapper -f -l scheduler-prune-on-get-work
complete -c luigi-wrapper -f -l scheduler-pause-enabled
complete -c luigi-wrapper -f -l scheduler-send-messages
complete -c luigi-wrapper -f -l scheduler-metrics-collector -r
complete -c luigi-wrapper -f -l scheduler-metrics-custom-import -r
complete -c luigi-wrapper -f -l scheduler-stable-done-cooldown-secs -r -d 'Sets cooldown period to avoid running the same task twice'
complete -c luigi-wrapper -f -l worker-id -r -d 'Override the auto-generated worker_id'
complete -c luigi-wrapper -f -l worker-ping-interval -r
complete -c luigi-wrapper -f -l worker-keep-alive
complete -c luigi-wrapper -f -l worker-count-uniques -d 'worker-count-uniques means that we will keep a worker alive only if it has a unique pending task, as well as having keep-alive true'
complete -c luigi-wrapper -f -l worker-count-last-scheduled -d 'Keep a worker alive only if there are pending tasks which it was the last to schedule.'
complete -c luigi-wrapper -f -l worker-wait-interval -r
complete -c luigi-wrapper -f -l worker-wait-jitter -r
complete -c luigi-wrapper -f -l worker-max-keep-alive-idle-duration -r
complete -c luigi-wrapper -f -l worker-max-reschedules -r
complete -c luigi-wrapper -f -l worker-timeout -r
complete -c luigi-wrapper -f -l worker-task-limit -r
complete -c luigi-wrapper -f -l worker-retry-external-tasks -d 'If true, incomplete external tasks will be retested for completion while Luigi is running.'
complete -c luigi-wrapper -f -l worker-send-failure-email -d 'If true, send e-mails directly from the workeron failure'
complete -c luigi-wrapper -f -l worker-no-install-shutdown-handler -d 'If true, the SIGUSR1 shutdown handler willNOT be install on the worker'
complete -c luigi-wrapper -f -l worker-check-unfulfilled-deps -d 'If true, check for completeness of dependencies before running a task'
complete -c luigi-wrapper -f -l worker-check-complete-on-run -d 'If true, only mark tasks as done after running if they are complete. Regardless of this setting, the worker will always check if external tasks are complete before marking them as done.'
complete -c luigi-wrapper -f -l worker-force-multiprocessing -d 'If true, use multiprocessing also when running with 1 worker'
complete -c luigi-wrapper -f -l worker-task-process-context -r -d 'If set to a fully qualified class name, the class will be instantiated with a TaskProcess as its constructor parameter and applied as a context manager around its run() call, so this can be used for obtaining high level customizable monitoring or logging of each individual Task run.'
complete -c luigi-wrapper -f -l worker-cache-task-completion -d 'If true, cache the response of successful completion checks of tasks assigned to a worker. This can especially speed up tasks with dynamic dependencies but assumes that the completion status does not change after it was true the first time.'
complete -c luigi-wrapper -f -l execution-summary-summary-length -r
complete -c luigi-wrapper -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -f -l scheduler-host -r -d 'Hostname of machine running remote scheduler'
complete -c luigi-wrapper -f -l scheduler-port -r -d 'Port of remote scheduler api process'
complete -c luigi-wrapper -f -l scheduler-url -r -d 'Full path to remote scheduler'
complete -c luigi-wrapper -f -l lock-size -r -d 'Maximum number of workers running the same command'
complete -c luigi-wrapper -f -l no-lock -d 'Ignore if similar process is already running'
complete -c luigi-wrapper -f -l lock-pid-dir -r -d 'Directory to store the pid file'
complete -c luigi-wrapper -f -l take-lock -d 'Signal other processes to stop getting work if already running'
complete -c luigi-wrapper -f -l workers -r -d 'Maximum number of parallel tasks to run'
complete -c luigi-wrapper -f -l logging-conf-file -r -d 'Configuration file for logging'
complete -c luigi-wrapper -f -l log-level -r -d 'Default log level to use when logging_conf_file is not set Choices: {WARNING, DEBUG, INFO, ERROR, CRITICAL, NOTSET}'
complete -c luigi-wrapper -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -f -l parallel-scheduling -d 'Use multiprocessing to do scheduling in parallel.'
complete -c luigi-wrapper -f -l parallel-scheduling-processes -r -d 'The number of processes to use for scheduling in parallel. By default the number of available CPUs will be used'
complete -c luigi-wrapper -f -l assistant -d 'Run any task from the scheduler.'
complete -c luigi-wrapper -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -f -l RangeBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeBase-start -r
complete -c luigi-wrapper -f -l RangeBase-stop -r
complete -c luigi-wrapper -f -l RangeBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeDailyBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeDailyBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeDailyBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeDailyBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeDailyBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeDailyBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeDailyBase-start -r -d 'beginning date, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeDailyBase-stop -r -d 'ending date, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeDailyBase-days-back -r -d 'extent to which contiguousness is to be assured into past, in days from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeDailyBase-days-forward -r -d 'extent to which contiguousness is to be assured into future, in days from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeHourlyBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeHourlyBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeHourlyBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeHourlyBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeHourlyBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeHourlyBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeHourlyBase-start -r -d 'beginning datehour, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeHourlyBase-stop -r -d 'ending datehour, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeHourlyBase-hours-back -r -d 'extent to which contiguousness is to be assured into past, in hours from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeHourlyBase-hours-forward -r -d 'extent to which contiguousness is to be assured into future, in hours from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeByMinutesBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeByMinutesBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeByMinutesBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeByMinutesBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeByMinutesBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeByMinutesBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeByMinutesBase-start -r -d 'beginning date-hour-minute, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeByMinutesBase-stop -r -d 'ending date-hour-minute, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeByMinutesBase-minutes-back -r -d 'extent to which contiguousness is to be assured into past, in minutes from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeByMinutesBase-minutes-forward -r -d 'extent to which contiguousness is to be assured into future, in minutes from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeByMinutesBase-minutes-interval -r -d 'separation between events in minutes. It must evenly divide 60'
complete -c luigi-wrapper -f -l RangeMonthly-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeMonthly-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeMonthly-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeMonthly-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeMonthly-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeMonthly-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeMonthly-start -r -d 'beginning month, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeMonthly-stop -r -d 'ending month, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeMonthly-months-back -r -d 'extent to which contiguousness is to be assured into past, in months from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeMonthly-months-forward -r -d 'extent to which contiguousness is to be assured into future, in months from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeDaily-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeDaily-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeDaily-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeDaily-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeDaily-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeDaily-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeDaily-start -r -d 'beginning date, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeDaily-stop -r -d 'ending date, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeDaily-days-back -r -d 'extent to which contiguousness is to be assured into past, in days from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeDaily-days-forward -r -d 'extent to which contiguousness is to be assured into future, in days from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeHourly-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeHourly-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeHourly-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeHourly-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeHourly-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeHourly-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeHourly-start -r -d 'beginning datehour, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeHourly-stop -r -d 'ending datehour, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeHourly-hours-back -r -d 'extent to which contiguousness is to be assured into past, in hours from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeHourly-hours-forward -r -d 'extent to which contiguousness is to be assured into future, in hours from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeByMinutes-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi-wrapper -f -l RangeByMinutes-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi-wrapper -f -l RangeByMinutes-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi-wrapper -f -l RangeByMinutes-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi-wrapper -f -l RangeByMinutes-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi-wrapper -f -l RangeByMinutes-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi-wrapper -f -l RangeByMinutes-start -r -d 'beginning date-hour-minute, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi-wrapper -f -l RangeByMinutes-stop -r -d 'ending date-hour-minute, exclusive. Default: None - work forward forever'
complete -c luigi-wrapper -f -l RangeByMinutes-minutes-back -r -d 'extent to which contiguousness is to be assured into past, in minutes from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi-wrapper -f -l RangeByMinutes-minutes-forward -r -d 'extent to which contiguousness is to be assured into future, in minutes from current time. Prevents infinite loop when stop is none'
complete -c luigi-wrapper -f -l RangeByMinutes-minutes-interval -r -d 'separation between events in minutes. It must evenly divide 60'
complete -c luigi-wrapper -f -l retcode-unhandled-exception -r -d 'For internal luigi errors.'
complete -c luigi-wrapper -f -l retcode-missing-data -r -d 'For when there are incomplete ExternalTask dependencies.'
complete -c luigi-wrapper -f -l retcode-task-failed -r -d 'For when a task'"'"'s run() method fails.'
complete -c luigi-wrapper -f -l retcode-already-running -r -d 'For both local --lock and luigid "lock"'
complete -c luigi-wrapper -f -l retcode-scheduling-error -r -d 'For when a task'"'"'s complete() or requires() fails, or task-limit reached'
complete -c luigi-wrapper -f -l retcode-not-run -r -d 'For when a task is not granted run permission by the scheduler.'
complete -c luigi-wrapper -f -l ExternalProgramTask-capture-output
complete -c luigi-wrapper -f -l ExternalProgramTask-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l ExternalProgramTask-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l ExternalPythonProgramTask-capture-output
complete -c luigi-wrapper -f -l ExternalPythonProgramTask-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l ExternalPythonProgramTask-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l ExternalPythonProgramTask-virtualenv -r -d 'path to the virtualenv directory to use. It should point to the directory containing the ``bin/activate`` file used for enabling the virtualenv.'
complete -c luigi-wrapper -f -l ExternalPythonProgramTask-extra-pythonpath -r -d 'extend the search path for modules by prepending this value to the ``PYTHONPATH`` environment variable.'
complete -c luigi-wrapper -f -l bioluigi-scheduler -r -d 'Default scheduler to use in ScheduledExternalProgram'
complete -c luigi-wrapper -f -l bioluigi-scheduler-partition -r -d 'Node partition to use for scheduling jobs if supported'
complete -c luigi-wrapper -f -l bioluigi-scheduler-extra-args -r -d 'List of extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l bioluigi-prefetch-bin -r
complete -c luigi-wrapper -f -l bioluigi-fastqdump-bin -r
complete -c luigi-wrapper -f -l bioluigi-cutadapt-bin -r
complete -c luigi-wrapper -f -l bioluigi-fastqc-bin -r
complete -c luigi-wrapper -f -l bioluigi-star-bin -r
complete -c luigi-wrapper -f -l bioluigi-rsem-dir -r
complete -c luigi-wrapper -f -l bioluigi-bcftools-bin -r
complete -c luigi-wrapper -f -l bioluigi-vep-bin -r
complete -c luigi-wrapper -f -l bioluigi-vep-dir -r
complete -c luigi-wrapper -f -l bioluigi-multiqc-bin -r
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-capture-output
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l ScheduledExternalProgramTask-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-capture-output
complete -c luigi-wrapper -f -l fastqc.GenerateReport-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l fastqc.GenerateReport-input-file -r
complete -c luigi-wrapper -f -l fastqc.GenerateReport-output-dir -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-capture-output
complete -c luigi-wrapper -f -l multiqc.GenerateReport-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l multiqc.GenerateReport-input-dirs -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-output-dir -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-sample-names -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-replace-names -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-title -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-comment -r
complete -c luigi-wrapper -f -l multiqc.GenerateReport-force
complete -c luigi-wrapper -f -l rnaseq-pipeline-GENOMES -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-OUTPUT-DIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-REFERENCES -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-METADATA -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-DATA -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-DATAQCDIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-ALIGNDIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-ALIGNQCDIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-QUANTDIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-BATCHINFODIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-RSEM-DIR -r
complete -c luigi-wrapper -f -l rnaseq-pipeline-SLACK-WEBHOOK-URL -r
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-capture-output
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-adapter-3prime -r
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-adapter-5prime -r
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-cut -r
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-trim-n
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-minimum-length -r
complete -c luigi-wrapper -f -l cutadapt.CutadaptTask-report-file -r -d 'Destination for the JSON report'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-capture-output
complete -c luigi-wrapper -f -l cutadapt.TrimReads-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-adapter-3prime -r
complete -c luigi-wrapper -f -l cutadapt.TrimReads-adapter-5prime -r
complete -c luigi-wrapper -f -l cutadapt.TrimReads-cut -r
complete -c luigi-wrapper -f -l cutadapt.TrimReads-trim-n
complete -c luigi-wrapper -f -l cutadapt.TrimReads-minimum-length -r
complete -c luigi-wrapper -f -l cutadapt.TrimReads-report-file -r -d 'Destination for the JSON report'
complete -c luigi-wrapper -f -l cutadapt.TrimReads-input-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimReads-output-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-capture-output
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-adapter-3prime -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-adapter-5prime -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-cut -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-trim-n
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-minimum-length -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-report-file -r -d 'Destination for the JSON report'
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-input-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-input2-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-output-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-output2-file -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-reverse-adapter-3prime -r
complete -c luigi-wrapper -f -l cutadapt.TrimPairedReads-reverse-adapter-5prime -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressFastq-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressFastq-fastq-url -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressSample-fastq-urls -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.arrayexpress.DownloadArrayExpressExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-baseurl -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-appdata-dir -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-cli-bin -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-cli-JAVA-HOME -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-cli-JAVA-OPTS -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-human-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-mouse-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma-rat-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma.GemmaCliTask-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma.GemmaCliTask-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma.GemmaCliTask-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.gemma.GemmaCliTask-experiment-id -r
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-capture-output
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-metadata -r
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-srr-accession -r
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-output-file -r
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-max-size -r -d 'Maximum download size in gigabytes'
complete -c luigi-wrapper -f -l sratoolkit.Prefetch-extra-args -r -d 'Extra arguments to pass to prefetch which can be used to setup Aspera'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-capture-output
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-cpus -r -d 'Number of CPUs to allocate for the task'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-memory -r -d 'Amount of memory (in gigabyte) to allocate for the task'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-metadata -r
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-input-file -r -d 'A file path or a SRA archive, or a SRA run accession'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-output-dir -r -d 'Destination directory for the extracted FASTQs'
complete -c luigi-wrapper -f -l sratoolkit.FastqDump-minimum-read-length -r -d 'Minimum read length to be extracted from the archive'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.PrefetchSraRun-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.PrefetchSraRun-srr -r -d 'SRA run identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DumpSraRun-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DumpSraRun-srr -r -d 'SRA run identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DumpSraRun-srx -r -d 'SRA experiment identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DumpSraRun-paired-reads -d 'Indicate of reads have paired or single mates'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperimentRunInfo-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperimentRunInfo-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperimentRunInfo-srx -r -d 'SRX accession to use'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-srx -r -d 'SRX accession to use'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-srr -r -d 'Specific SRA run accession to use (defaults to latest)'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-force-single-end -d 'Force the library layout to be single-end'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraExperiment-force-paired-reads -d 'Force the library layout to be paired'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProjectRunInfo-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProjectRunInfo-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProjectRunInfo-srp -r -d 'SRA project identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProject-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProject-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProject-srp -r -d 'SRA project identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.DownloadSraProject-ignored-samples -r -d 'Ignored SRX identifiers'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.ExtractSraProjectBatchInfo-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.ExtractSraProjectBatchInfo-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.ExtractSraProjectBatchInfo-srp -r -d 'SRA project identifier'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.sra.ExtractSraProjectBatchInfo-ignored-samples -r -d 'Ignored SRX identifiers'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSampleMetadata-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSampleMetadata-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSampleMetadata-gsm -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSample-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSample-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSample-gsm -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeriesMetadata-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeriesMetadata-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeriesMetadata-gse -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeries-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeries-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeries-gse -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.DownloadGeoSeries-ignored-samples -r -d 'Ignored GSM identifiers'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.ExtractGeoSeriesBatchInfo-metadata -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.ExtractGeoSeriesBatchInfo-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.ExtractGeoSeriesBatchInfo-gse -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.geo.ExtractGeoSeriesBatchInfo-ignored-samples -r -d 'Ignored GSM identifiers'
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.gemma.DownloadGemmaExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.gemma.ExtractGemmaExperimentBatchInfo-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.local.DownloadLocalSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.local.DownloadLocalSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.sources.local.DownloadLocalExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.DownloadSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.DownloadSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.DownloadSample-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.DownloadExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.DownloadExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimSample-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimSample-ignore-mate -r -d 'Choices: {forward, reverse, neither}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimSample-minimum-length -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.TrimExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlSample-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlSample-ignore-mate -r -d 'Choices: {forward, reverse, neither}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlSample-minimum-length -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.QualityControlExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.PrepareReference-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-sample-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-ignore-mate -r -d 'Choices: {forward, reverse, neither}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-minimum-length -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-strand-specific
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignSample-scope -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignExperiment-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignExperiment-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.AlignExperiment-scope -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-scope -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.CountExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.CountExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.CountExperiment-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.CountExperiment-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.CountExperiment-scope -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, sra, geo}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-taxon -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-reference-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-scope -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperiment-priority -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-ignored-samples -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-priority -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-capture-output
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-experiment-id -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-rerun
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-ignored-samples -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-priority -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromFileToGemma-ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromFileToGemma-input-file -r
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-spreadsheet-id -r -d 'Spreadsheet ID in Google Sheets (lookup {spreadsheetId} in https://docs.google.com/spreadsheet s/d/{spreadsheetId}/edit)'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-sheet-name -r -d 'Name of the spreadsheet in the document'
complete -c luigi-wrapper -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-revision-id -r -d 'Revision ID of the spreadsheet (not yet supported, but will default to the latest)'
complete -c luigi-wrapper -n 'not __fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment rnaseq_pipeline.tasks.AlignSample rnaseq_pipeline.tasks.CountExperiment rnaseq_pipeline.tasks.DownloadExperiment rnaseq_pipeline.tasks.DownloadSample rnaseq_pipeline.tasks.GenerateReportForExperiment rnaseq_pipeline.tasks.PrepareReference rnaseq_pipeline.tasks.QualityControlExperiment rnaseq_pipeline.tasks.QualityControlSample rnaseq_pipeline.tasks.SubmitExperiment rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma rnaseq_pipeline.tasks.SubmitExperimentDataToGemma rnaseq_pipeline.tasks.SubmitExperimentReportToGemma rnaseq_pipeline.tasks.SubmitExperimentToGemma rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma rnaseq_pipeline.tasks.TrimExperiment rnaseq_pipeline.tasks.TrimSample' -a 'rnaseq_pipeline.tasks.AlignExperiment rnaseq_pipeline.tasks.AlignSample rnaseq_pipeline.tasks.CountExperiment rnaseq_pipeline.tasks.DownloadExperiment rnaseq_pipeline.tasks.DownloadSample rnaseq_pipeline.tasks.GenerateReportForExperiment rnaseq_pipeline.tasks.PrepareReference rnaseq_pipeline.tasks.QualityControlExperiment rnaseq_pipeline.tasks.QualityControlSample rnaseq_pipeline.tasks.SubmitExperiment rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma rnaseq_pipeline.tasks.SubmitExperimentDataToGemma rnaseq_pipeline.tasks.SubmitExperimentReportToGemma rnaseq_pipeline.tasks.SubmitExperimentToGemma rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma rnaseq_pipeline.tasks.TrimExperiment rnaseq_pipeline.tasks.TrimSample'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l rnaseq-pipeline.tasks.AlignExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l rnaseq-pipeline.tasks.AlignExperiment-source -r -d 'Choices: {gemma, local, arrayexpress, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l source -r -d 'Choices: {gemma, local, arrayexpress, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l rnaseq-pipeline.tasks.AlignExperiment-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l rnaseq-pipeline.tasks.AlignExperiment-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l rnaseq-pipeline.tasks.AlignExperiment-scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignExperiment' -f -l scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {none, stdout, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {none, stdout, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-source -r -d 'Choices: {gemma, local, arrayexpress, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l source -r -d 'Choices: {gemma, local, arrayexpress, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-ignore-mate -r -d 'Choices: {reverse, neither, forward}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l ignore-mate -r -d 'Choices: {reverse, neither, forward}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-minimum-length -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l minimum-length -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-strand-specific
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l strand-specific
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l rnaseq-pipeline.tasks.AlignSample-scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.AlignSample' -f -l scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l rnaseq-pipeline.tasks.CountExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l rnaseq-pipeline.tasks.CountExperiment-source -r -d 'Choices: {arrayexpress, local, gemma, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l source -r -d 'Choices: {arrayexpress, local, gemma, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l rnaseq-pipeline.tasks.CountExperiment-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l rnaseq-pipeline.tasks.CountExperiment-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l rnaseq-pipeline.tasks.CountExperiment-scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.CountExperiment' -f -l scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l rnaseq-pipeline.tasks.DownloadExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l rnaseq-pipeline.tasks.DownloadExperiment-source -r -d 'Choices: {local, sra, arrayexpress, geo, gemma}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadExperiment' -f -l source -r -d 'Choices: {local, sra, arrayexpress, geo, gemma}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l rnaseq-pipeline.tasks.DownloadSample-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l rnaseq-pipeline.tasks.DownloadSample-sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l rnaseq-pipeline.tasks.DownloadSample-source -r -d 'Choices: {sra, geo, arrayexpress, gemma, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.DownloadSample' -f -l source -r -d 'Choices: {sra, geo, arrayexpress, gemma, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-source -r -d 'Choices: {local, arrayexpress, gemma, sra, geo}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l source -r -d 'Choices: {local, arrayexpress, gemma, sra, geo}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l rnaseq-pipeline.tasks.GenerateReportForExperiment-scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.GenerateReportForExperiment' -f -l scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stdout, stderr, none}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stdout, stderr, none}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l scheduler -r -d 'Scheduler to use for running the task Choices: {slurm, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l scheduler-partition -r -d 'Scheduler partition (or queue) to use if supported'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l scheduler-extra-args -r -d 'Extra arguments to pass to the scheduler'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l walltime -r -d 'Amout of time to allocate for the task, default value of zero implies unlimited time'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l rnaseq-pipeline.tasks.PrepareReference-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.PrepareReference' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l rnaseq-pipeline.tasks.QualityControlExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l rnaseq-pipeline.tasks.QualityControlExperiment-source -r -d 'Choices: {geo, gemma, local, sra, arrayexpress}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlExperiment' -f -l source -r -d 'Choices: {geo, gemma, local, sra, arrayexpress}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l rnaseq-pipeline.tasks.QualityControlSample-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l rnaseq-pipeline.tasks.QualityControlSample-sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l rnaseq-pipeline.tasks.QualityControlSample-source -r -d 'Choices: {geo, gemma, arrayexpress, local, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l source -r -d 'Choices: {geo, gemma, arrayexpress, local, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l rnaseq-pipeline.tasks.QualityControlSample-ignore-mate -r -d 'Choices: {forward, neither, reverse}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l ignore-mate -r -d 'Choices: {forward, neither, reverse}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l rnaseq-pipeline.tasks.QualityControlSample-minimum-length -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.QualityControlSample' -f -l minimum-length -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-source -r -d 'Choices: {geo, sra, gemma, arrayexpress, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l source -r -d 'Choices: {geo, sra, gemma, arrayexpress, local}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l taxon -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l reference-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l scope -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l rnaseq-pipeline.tasks.SubmitExperiment-priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperiment' -f -l priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {none, stdout, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {none, stdout, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentBatchInfoToGemma-ignored-samples -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentBatchInfoToGemma' -f -l ignored-samples -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stdout, none, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stdout, none, stderr}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentDataToGemma-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentDataToGemma' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentReportToGemma-priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentReportToGemma' -f -l priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l capture-output
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l stream-for-searching-tracking-url -r -d 'Stream for searching tracking URL Choices: {stderr, none, stdout}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l tracking-url-pattern -r -d 'Regex pattern used for searching URL in the logs of the external program'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rerun
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-ignored-samples -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l ignored-samples -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentToGemma-priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentToGemma' -f -l priority -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromFileToGemma-ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromFileToGemma-input-file -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromFileToGemma' -f -l input-file -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l ignore-priority -d 'Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-spreadsheet-id -r -d 'Spreadsheet ID in Google Sheets (lookup {spreadsheetId} in https://docs.google.com/spreadsheet s/d/{spreadsheetId}/edit)'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l spreadsheet-id -r -d 'Spreadsheet ID in Google Sheets (lookup {spreadsheetId} in https://docs.google.com/spreadsheet s/d/{spreadsheetId}/edit)'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-sheet-name -r -d 'Name of the spreadsheet in the document'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l sheet-name -r -d 'Name of the spreadsheet in the document'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l rnaseq-pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma-revision-id -r -d 'Revision ID of the spreadsheet (not yet supported, but will default to the latest)'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma' -f -l revision-id -r -d 'Revision ID of the spreadsheet (not yet supported, but will default to the latest)'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l rnaseq-pipeline.tasks.TrimExperiment-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l rnaseq-pipeline.tasks.TrimExperiment-source -r -d 'Choices: {gemma, arrayexpress, local, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimExperiment' -f -l source -r -d 'Choices: {gemma, arrayexpress, local, geo, sra}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l help-all -d 'Show all command line flags'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l rnaseq-pipeline.tasks.TrimSample-experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l experiment-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l rnaseq-pipeline.tasks.TrimSample-sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l sample-id -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l rnaseq-pipeline.tasks.TrimSample-source -r -d 'Choices: {local, geo, sra, arrayexpress, gemma}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l source -r -d 'Choices: {local, geo, sra, arrayexpress, gemma}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l rnaseq-pipeline.tasks.TrimSample-ignore-mate -r -d 'Choices: {neither, forward, reverse}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l ignore-mate -r -d 'Choices: {neither, forward, reverse}'
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l rnaseq-pipeline.tasks.TrimSample-minimum-length -r
complete -c luigi-wrapper -n '__fish_seen_subcommand_from rnaseq_pipeline.tasks.TrimSample' -f -l minimum-length -r
