import os
import re
import json
import typer
import ollama
from typing import Dict, Any
import tools 

app = typer.Typer()

class AgentRunner:
    def __init__(self, model_name: str, max_cycles: int = 15):
        self.model_name = model_name
        self.max_cycles = max_cycles
        self.context_files = ["AGENT_SCHEMA.md", "llm-wiki.md"]
        self.system_prompt = self._assemble_prompt()
        
        self.tool_registry: Dict[str, Any] = {
            "read_document": tools.read_document,
            "write_file": tools.write_file,
            "append_to_file": tools.append_to_file,
            "search_wiki": tools.search_wiki,
            "get_file_metadata": tools.get_file_metadata,
            "list_directory": tools.list_directory,
            "web_scrape": tools.web_scrape,
            "check_broken_links": tools.check_broken_links,
            "find_orphan_pages": tools.find_orphan_pages,
            "rebuild_index": tools.rebuild_wiki_index,
        }

    def _assemble_prompt(self) -> str:
        combined_context = ["You are a Wiki Librarian. Follow the LLM-Wiki pattern: Thought/Action/Input/Observation/Response."]
        for file_path in self.context_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    combined_context.append(f.read())
        return "\n\n".join(combined_context)

    def parse_llm_output(self, text: str) -> Dict[str, str]:
        patterns = {
            "thought": r"Thought:\s*(.*?)(?=\nAction:|\nResponse:|$)",
            "action": r"Action:\s*(.*?)(?=\nInput:|\nResponse:|$)",
            "input": r"Input:\s*(\{.*?\})",
            "response": r"Response:\s*(.*)"
        }
        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            extracted[key] = match.group(1).strip() if match else None
        return extracted

    def execute_tool(self, action_name: str, tool_input: str) -> str:
        if action_name not in self.tool_registry:
            return f"Error: Tool '{action_name}' is not registered."
        try:
            params = json.loads(tool_input)
            return self.tool_registry[action_name](**params)
        except Exception as e:
            return f"Error: {str(e)}"

    def run_session(self):
        typer.echo(f"🚀 LLM-Wiki Engine Started [{self.model_name}]")
        messages = [{"role": "system", "content": self.system_prompt}]

        while True:
            user_input = typer.prompt("User")
            if user_input.lower() in ["exit", "quit"]: break

            messages.append({"role": "user", "content": user_input})
            
            for _ in range(self.max_cycles):
                response = ollama.chat(model=self.model_name, messages=messages)
                assistant_text = response['message']['content']
                messages.append({"role": "assistant", "content": assistant_text})
                
                parsed = self.parse_llm_output(assistant_text)

                # If the agent is done, show the final response to user
                if parsed.get("response"):
                    typer.secho(f"\n[Agent]: {parsed['response']}", fg=typer.colors.GREEN)
                    break

                # If the agent wants to take an action
                if parsed.get("action") and parsed.get("input"):
                    action = parsed["action"]
                    typer.secho(f"🛠️  Action: {action}", fg=typer.colors.CYAN)
                    
                    observation = self.execute_tool(action, parsed["input"])
                    typer.echo(f"👁️  Observation: {observation[:200]}...") # Truncate for terminal clarity
                    
                    # Feed the result back as a "user" role so the model processes the result
                    messages.append({"role": "user", "content": f"Observation: {observation}"})
                else:
                    # Fallback if the LLM doesn't follow formatting strictly
                    typer.echo(f"\n[Agent]: {assistant_text}")
                    break

if __name__ == "__main__":
    # Ensure a basic wiki structure exists
    os.makedirs("wiki", exist_ok=True)
    os.makedirs("raw", exist_ok=True)
    
    runner = AgentRunner(model_name="gemma4-stable") # Or your preferred local model
    runner.run_session()