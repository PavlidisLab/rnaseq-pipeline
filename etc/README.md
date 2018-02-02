# What's in here?

This pipeline intended to be easy to configure and flexible to different system set-ups.

In this directory, you should have a `common.cfg` file which represents the basic paths and settings needed for this pipeline to run. See `common.cfg.EXAMPLE` for a sample configuration set-up.

The `etc/modes` directory contains a handful of additional configuration files. Anytime the pipeline is launched with `MODES="something1,something2"`, the configuration files `something1.cfg` and `something2.cfg` are sucessively loaded and can override configurations in `common.cfg`. The idea is that common.cfg is your general, basic case, and modes can be used to do special tasks. For example, `distributed.cfg` adds multiple machines/workers to process samples in parallel, while `human.cfg` sets the assembly to a human assembly (instead of the default one set in `common.cfg`).

