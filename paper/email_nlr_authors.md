# Draft email to the NLR dataset authors (for you to send)

To: corresponding author of arXiv:2604.07345 (check the paper / data.nlr.gov submission 312 for the address)
Subject: Question on GPU power sampling in the "Dataset of Generative AI Workload Power Profiles"

Dear Dr. Vercellino and co-authors,

Thank you for publishing the Generative AI Workload Power Profiles dataset (NLR submission 312). We are
using it, with citation, in a study of short-horizon prediction of GPU power ramps for data-center power
smoothing.

We have one question about the GPU logs in 00_raw_datasets (nvml_wattameter_*.log): which NVML call
does WattAMeter use for the gpu-N[mW] columns? On Hopper GPUs, nvmlDeviceGetPowerUsage returns a power
value averaged over roughly one second, while the instantaneous field (NVML_FI_DEV_POWER_INSTANT, or
power.draw.instant in nvidia-smi) updates much faster. In the raw logs, large falls typically take
about 1 to 1.5 s and the largest single 0.2 s step is about a quarter to a third of the full fall, which
would be consistent with averaging, but we would rather confirm than assume.

Knowing this would let us state correctly how fast the measured ramps are. If the WattAMeter source is
public, a pointer to it would also be very helpful.

Thank you again for making the data available.

Best regards,
[Your name]
[Affiliation / company]
[Email]
