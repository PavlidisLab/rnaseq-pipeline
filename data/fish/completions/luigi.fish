complete -c luigi -e
complete -c luigi -f
complete -c luigi -f -l TestNotificationsTask-raise-in-complete -d 'If true, fail in complete() instead of run()'
complete -c luigi -f -l email-force-send -d 'Send e-mail even from a tty'
complete -c luigi -f -l email-format -r -d 'Format type for sent e-mails Choices: {plain, html, none}'
complete -c luigi -f -l email-method -r -d 'Method for sending e-mail Choices: {smtp, ses, sendgrid, sns}'
complete -c luigi -f -l email-prefix -r -d 'Prefix for subject lines of all e-mails'
complete -c luigi -f -l email-receiver -r -d 'Address to send error e-mails to'
complete -c luigi -f -l email-traceback-max-length -r -d 'Max length for error traceback'
complete -c luigi -f -l email-sender -r -d 'Address to send e-mails from'
complete -c luigi -f -l smtp-host -r -d 'Hostname of smtp server'
complete -c luigi -f -l smtp-local-hostname -r -d 'If specified, local_hostname is used as the FQDN of the local host in the HELO/EHLO command'
complete -c luigi -f -l smtp-no-tls -d 'Do not use TLS in SMTP connections'
complete -c luigi -f -l smtp-password -r -d 'Password for the SMTP server login'
complete -c luigi -f -l smtp-port -r -d 'Port number for smtp server'
complete -c luigi -f -l smtp-ssl -d 'Use SSL for the SMTP connection.'
complete -c luigi -f -l smtp-timeout -r -d 'Number of seconds before timing out the smtp connection'
complete -c luigi -f -l smtp-username -r -d 'Username used to log in to the SMTP host'
complete -c luigi -f -l sendgrid-apikey -r -d 'API key for SendGrid login'
complete -c luigi -f -l batch-email-email-interval -r -d 'Number of minutes between e-mail sends (default: 60)'
complete -c luigi -f -l batch-email-batch-mode -r -d 'Method used for batching failures in e-mail. If "family" all failures for tasks with the same family will be batched. If "unbatched_params", all failures for tasks with the same family and non-batched parameters will be batched. If "all", tasks will only be batched if they have identical names. Choices: {family, all, unbatched_params}'
complete -c luigi -f -l batch-email-error-lines -r -d 'Number of lines to show from each error message. 0 means show all'
complete -c luigi -f -l batch-email-error-messages -r -d 'Number of error messages to show for each group'
complete -c luigi -f -l batch-email-group-by-error-messages -d 'Group items with the same error messages together'
complete -c luigi -f -l scheduler-retry-delay -r
complete -c luigi -f -l scheduler-remove-delay -r
complete -c luigi -f -l scheduler-worker-disconnect-delay -r
complete -c luigi -f -l scheduler-state-path -r
complete -c luigi -f -l scheduler-batch-emails -d 'Send e-mails in batches rather than immediately'
complete -c luigi -f -l scheduler-disable-window -r
complete -c luigi -f -l scheduler-retry-count -r
complete -c luigi -f -l scheduler-disable-hard-timeout -r
complete -c luigi -f -l scheduler-disable-persist -r
complete -c luigi -f -l scheduler-max-shown-tasks -r
complete -c luigi -f -l scheduler-max-graph-nodes -r
complete -c luigi -f -l scheduler-record-task-history
complete -c luigi -f -l scheduler-prune-on-get-work
complete -c luigi -f -l scheduler-pause-enabled
complete -c luigi -f -l scheduler-send-messages
complete -c luigi -f -l scheduler-metrics-collector -r
complete -c luigi -f -l scheduler-metrics-custom-import -r
complete -c luigi -f -l scheduler-stable-done-cooldown-secs -r -d 'Sets cooldown period to avoid running the same task twice'
complete -c luigi -f -l worker-id -r -d 'Override the auto-generated worker_id'
complete -c luigi -f -l worker-ping-interval -r
complete -c luigi -f -l worker-keep-alive
complete -c luigi -f -l worker-count-uniques -d 'worker-count-uniques means that we will keep a worker alive only if it has a unique pending task, as well as having keep-alive true'
complete -c luigi -f -l worker-count-last-scheduled -d 'Keep a worker alive only if there are pending tasks which it was the last to schedule.'
complete -c luigi -f -l worker-wait-interval -r
complete -c luigi -f -l worker-wait-jitter -r
complete -c luigi -f -l worker-max-keep-alive-idle-duration -r
complete -c luigi -f -l worker-max-reschedules -r
complete -c luigi -f -l worker-timeout -r
complete -c luigi -f -l worker-task-limit -r
complete -c luigi -f -l worker-retry-external-tasks -d 'If true, incomplete external tasks will be retested for completion while Luigi is running.'
complete -c luigi -f -l worker-send-failure-email -d 'If true, send e-mails directly from the workeron failure'
complete -c luigi -f -l worker-no-install-shutdown-handler -d 'If true, the SIGUSR1 shutdown handler willNOT be install on the worker'
complete -c luigi -f -l worker-check-unfulfilled-deps -d 'If true, check for completeness of dependencies before running a task'
complete -c luigi -f -l worker-check-complete-on-run -d 'If true, only mark tasks as done after running if they are complete. Regardless of this setting, the worker will always check if external tasks are complete before marking them as done.'
complete -c luigi -f -l worker-force-multiprocessing -d 'If true, use multiprocessing also when running with 1 worker'
complete -c luigi -f -l worker-task-process-context -r -d 'If set to a fully qualified class name, the class will be instantiated with a TaskProcess as its constructor parameter and applied as a context manager around its run() call, so this can be used for obtaining high level customizable monitoring or logging of each individual Task run.'
complete -c luigi -f -l worker-cache-task-completion -d 'If true, cache the response of successful completion checks of tasks assigned to a worker. This can especially speed up tasks with dynamic dependencies but assumes that the completion status does not change after it was true the first time.'
complete -c luigi -f -l execution-summary-summary-length -r
complete -c luigi -f -l local-scheduler -d 'Use an in-memory central scheduler. Useful for testing.'
complete -c luigi -f -l scheduler-host -r -d 'Hostname of machine running remote scheduler'
complete -c luigi -f -l scheduler-port -r -d 'Port of remote scheduler api process'
complete -c luigi -f -l scheduler-url -r -d 'Full path to remote scheduler'
complete -c luigi -f -l lock-size -r -d 'Maximum number of workers running the same command'
complete -c luigi -f -l no-lock -d 'Ignore if similar process is already running'
complete -c luigi -f -l lock-pid-dir -r -d 'Directory to store the pid file'
complete -c luigi -f -l take-lock -d 'Signal other processes to stop getting work if already running'
complete -c luigi -f -l workers -r -d 'Maximum number of parallel tasks to run'
complete -c luigi -f -l logging-conf-file -r -d 'Configuration file for logging'
complete -c luigi -f -l log-level -r -d 'Default log level to use when logging_conf_file is not set Choices: {NOTSET, WARNING, ERROR, CRITICAL, INFO, DEBUG}'
complete -c luigi -f -l module -r -d 'Used for dynamic loading of modules'
complete -c luigi -f -l parallel-scheduling -d 'Use multiprocessing to do scheduling in parallel.'
complete -c luigi -f -l parallel-scheduling-processes -r -d 'The number of processes to use for scheduling in parallel. By default the number of available CPUs will be used'
complete -c luigi -f -l assistant -d 'Run any task from the scheduler.'
complete -c luigi -f -l help -d 'Show most common flags and all task-specific flags'
complete -c luigi -f -l help-all -d 'Show all command line flags'
complete -c luigi -f -l RangeBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeBase-start -r
complete -c luigi -f -l RangeBase-stop -r
complete -c luigi -f -l RangeBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeDailyBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeDailyBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeDailyBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeDailyBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeDailyBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeDailyBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeDailyBase-start -r -d 'beginning date, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeDailyBase-stop -r -d 'ending date, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeDailyBase-days-back -r -d 'extent to which contiguousness is to be assured into past, in days from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeDailyBase-days-forward -r -d 'extent to which contiguousness is to be assured into future, in days from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeHourlyBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeHourlyBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeHourlyBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeHourlyBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeHourlyBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeHourlyBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeHourlyBase-start -r -d 'beginning datehour, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeHourlyBase-stop -r -d 'ending datehour, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeHourlyBase-hours-back -r -d 'extent to which contiguousness is to be assured into past, in hours from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeHourlyBase-hours-forward -r -d 'extent to which contiguousness is to be assured into future, in hours from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeByMinutesBase-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeByMinutesBase-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeByMinutesBase-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeByMinutesBase-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeByMinutesBase-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeByMinutesBase-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeByMinutesBase-start -r -d 'beginning date-hour-minute, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeByMinutesBase-stop -r -d 'ending date-hour-minute, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeByMinutesBase-minutes-back -r -d 'extent to which contiguousness is to be assured into past, in minutes from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeByMinutesBase-minutes-forward -r -d 'extent to which contiguousness is to be assured into future, in minutes from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeByMinutesBase-minutes-interval -r -d 'separation between events in minutes. It must evenly divide 60'
complete -c luigi -f -l RangeMonthly-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeMonthly-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeMonthly-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeMonthly-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeMonthly-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeMonthly-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeMonthly-start -r -d 'beginning month, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeMonthly-stop -r -d 'ending month, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeMonthly-months-back -r -d 'extent to which contiguousness is to be assured into past, in months from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeMonthly-months-forward -r -d 'extent to which contiguousness is to be assured into future, in months from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeDaily-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeDaily-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeDaily-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeDaily-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeDaily-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeDaily-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeDaily-start -r -d 'beginning date, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeDaily-stop -r -d 'ending date, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeDaily-days-back -r -d 'extent to which contiguousness is to be assured into past, in days from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeDaily-days-forward -r -d 'extent to which contiguousness is to be assured into future, in days from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeHourly-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeHourly-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeHourly-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeHourly-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeHourly-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeHourly-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeHourly-start -r -d 'beginning datehour, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeHourly-stop -r -d 'ending datehour, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeHourly-hours-back -r -d 'extent to which contiguousness is to be assured into past, in hours from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeHourly-hours-forward -r -d 'extent to which contiguousness is to be assured into future, in hours from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeByMinutes-of -r -d 'task name to be completed. The task must take a single datetime parameter'
complete -c luigi -f -l RangeByMinutes-of-params -r -d 'Arguments to be provided to the '"'"'of'"'"' class when instantiating'
complete -c luigi -f -l RangeByMinutes-reverse -d 'specifies the preferred order for catching up. False - work from the oldest missing outputs onward; True - from the newest backward'
complete -c luigi -f -l RangeByMinutes-task-limit -r -d 'how many of '"'"'of'"'"' tasks to require. Guards against scheduling insane amounts of tasks in one go'
complete -c luigi -f -l RangeByMinutes-now -r -d 'set to override current time. In seconds since epoch'
complete -c luigi -f -l RangeByMinutes-param-name -r -d 'parameter name used to pass in parameterized value. Defaults to None, meaning use first positional parameter'
complete -c luigi -f -l RangeByMinutes-start -r -d 'beginning date-hour-minute, inclusive. Default: None - work backward forever (requires reverse=True)'
complete -c luigi -f -l RangeByMinutes-stop -r -d 'ending date-hour-minute, exclusive. Default: None - work forward forever'
complete -c luigi -f -l RangeByMinutes-minutes-back -r -d 'extent to which contiguousness is to be assured into past, in minutes from current time. Prevents infinite loop when start is none. If the dataset has limited retention (i.e. old outputs get removed), this should be set shorter to that, too, to prevent the oldest outputs flapping. Increase freely if you intend to process old dates - worker'"'"'s memory is the limit'
complete -c luigi -f -l RangeByMinutes-minutes-forward -r -d 'extent to which contiguousness is to be assured into future, in minutes from current time. Prevents infinite loop when stop is none'
complete -c luigi -f -l RangeByMinutes-minutes-interval -r -d 'separation between events in minutes. It must evenly divide 60'
complete -c luigi -f -l retcode-unhandled-exception -r -d 'For internal luigi errors.'
complete -c luigi -f -l retcode-missing-data -r -d 'For when there are incomplete ExternalTask dependencies.'
complete -c luigi -f -l retcode-task-failed -r -d 'For when a task'"'"'s run() method fails.'
complete -c luigi -f -l retcode-already-running -r -d 'For both local --lock and luigid "lock"'
complete -c luigi -f -l retcode-scheduling-error -r -d 'For when a task'"'"'s complete() or requires() fails, or task-limit reached'
complete -c luigi -f -l retcode-not-run -r -d 'For when a task is not granted run permission by the scheduler.'
