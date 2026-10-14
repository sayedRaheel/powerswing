# Powerswing Resources

## Knowledge
- [Paper: Vercellino et al., "Measurement of Generative AI Workload Power Profiles for Whole-Facility Data Center Infrastructure Planning", arXiv 2604.07345](https://arxiv.org/abs/2604.07345)
  The paper behind our dataset. Use for: how the data was measured, hardware, benchmarks.
- [Dataset page: NLR submission 312](https://data.nlr.gov/submissions/312) (mirror: [OpenEI 8651](https://data.openei.org/submissions/8651))
  License (CC BY 4.0), files, citation request. Use for: what is officially in the dataset.
- [Paper: "Power Stabilization for AI Training Datacenters" (Microsoft, OpenAI, NVIDIA), arXiv 2508.14318](https://arxiv.org/abs/2508.14318)
  Why training power swings matter for the grid and the three fix families (software fill, GPU floor, storage). Use for: the problem framing and the always-burn idea.
- [MLCommons MLPerf Training](https://mlcommons.org/benchmarks/training/)
  The benchmark suite that produced the Llama2 LoRA and Stable Diffusion training jobs.
- [vLLM benchmarks](https://docs.vllm.ai/)
  The inference server and benchmark scripts behind the three inference workloads.
- [NVIDIA NVML API](https://docs.nvidia.com/deploy/nvml-api/)
  The GPU power counter the data was read from.
- Local: `data/README_data.md`, `reports/results.md`
  Our own documentation and results. Use for: exact numbers.

## Wisdom (Communities)
- [Climate Change AI community](https://www.climatechange.ai/community)
  ML + energy researchers. Use for: feedback on the paper angle.
- [r/datacenter](https://www.reddit.com/r/datacenter/)
  Operators. Use for: sanity checks on what smoothing hardware really costs and how fast it reacts.

## Gaps
- No public source yet on real actuator latency of GPU fill or rack batteries (needed for lesson 0005).
