# Output Directory

## Structure

| Folder | Description |
|--------|-------------|
| `generated_code1-3` | Simple demos |
| `generated_code4_DeepResearch-pdf_gemini-flash-lite-latest` | Test output using `gemini-flash-lite-latest` |
| `generated_code5_DeepResearch-pdf_Gemini-flash-latest` | Test output using `gemini-flash-latest` |
| `generated_code5_DeepResearch-pdf_Gemini-3-pro-preview` |  Test output using `gemini-3-pro-preview` |

## Benchmark

**Test Command:**
```powershell
uv run --env-file .env python run.py --prompt "Read DeepResearch.pdf first, design a possible architecture to demonstrate that, output including a complete code repo and a README.md" --references agent_competition_examples/references
```

**Timing Results:**

| Model | Duration | Output Folder |
|-------|----------|---------------|
| `gemini-flash-lite-latest` | ~10 min | `generated_code4_DeepResearch-pdf_gemini-flash-lite-latest` |
| `gemini-flash-latest` | ~35 min | `generated_code5_DeepResearch-pdf_Gemini-flash-latest` |
| `gemini-3-pro-preview | ~ 90 min | `generated_code6_DeepResearch-pdf_Gemini-3-pro-preview` |