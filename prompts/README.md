# Prompts of the Ad Studio's AI director

Plain-text copies of the prompts the live app sends to its LLM (google/gemma-4-31b-it on OpenRouter), for reading and sharing.
The code in `web_ec2/ad_director.py` is the source of truth; copy again after changing it.

| File | Used when | In the code |
|---|---|---|
| [master_prompt.txt](master_prompt.txt) | Making an ad from one line ("AI decides"). Also lists what is added to every AI picture prompt and what Python checks afterwards | `PLAN_SYSTEM` |
| [template_prompt.txt](template_prompt.txt) | Making an ad from a chosen template: the AI writes only the words | `TEMPLATE_SYSTEM` |
| [edit_prompt.txt](edit_prompt.txt) | A typed edit at a moment of the ad ("make this text bigger") | `EDIT_SYSTEM` |

The prompt for generating new templates with Antigravity or Gemini is in [docs/12-antigravity-template-prompt.md](../docs/12-antigravity-template-prompt.md).
