import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Tool Definitions (Restructured for Responses API)
TOOLS = [
    {
        "type": "function",
        "name": "create_project",
        "description": "Create a new project.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"}
            },
            "additionalProperties": False,
            "required": ["title"]
        }
    },
    {
        "type": "function",
        "name": "delete_project",
        "description": "Delete an existing project by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"}
            },
            "additionalProperties": False,
            "required": ["project_id"]
        }
    },
    {
        "type": "function",
        "name": "update_user_profile",
        "description": "Update the user's name, goals, or long-term notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "goals": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string", "description": "Long-term considerations, preferences, or notes about the user."}
            },
            "additionalProperties": False,
            "required": []
        }
    },
    {
        "type": "function",
        "name": "update_project_plan",
        "description": "Create or rewrite the tasks for a specific project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique ID"},
                            "title": {"type": "string"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                            "due_date": {"type": "string", "description": "YYYY-MM-DD or 'Next Week'"},
                            "subtasks": {
                                "type": "array",
                                "items": {"type": "object", "properties": {"title": {"type": "string"}}, "additionalProperties": False, "required": ["title"]}
                            }
                        },
                        "additionalProperties": False,
                        "required": ["title", "priority"]
                    }
                }
            },
            "additionalProperties": False,
            "required": ["project_id", "tasks"]
        }
    },
    {
        "type": "function",
        "name": "add_project_subtasks",
        "description": "Add subtasks to a specific task in a project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "task_index": {"type": "integer", "description": "Index of the parent task (0-based)"},
                "subtasks": {
                    "type": "array",
                    "items": {"type": "string", "description": "Subtask title"}
                }
            },
            "additionalProperties": False,
            "required": ["project_id", "task_index", "subtasks"]
        }
    },
    {
        "type": "function",
        "name": "mark_project_task_complete",
        "description": "Mark a task as completed in a project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "task_index": {"type": "integer", "description": "Index of the task (0-based)"}
            },
            "additionalProperties": False,
            "required": ["project_id", "task_index"]
        }
    }
]

from datetime import datetime

SYSTEM_Base = """
You are the AI Accountability Coach: friendly, direct, minimal, and practical.

Your job is to help the user turn intentions into clear next steps without overwhelming them.

Style:
- Keep responses concise by default.
- Give the shortest useful answer that still feels complete.
- Be warm, calm, and human, not overly enthusiastic, not robotic.
- Match the user's vibe and wording style.
- Avoid long explanations, long roadmaps, and heavy formatting unless the user asks for them.
- Do not use bold headers or large structured blocks unless necessary.

Conversation flow:
- Ask one question at a time.
- Do not interrogate.
- If you already have enough information to help, help first.
- If something important is missing, ask only for the single next detail that matters most.
- Do not ask unnecessary follow-up questions.

Planning behavior:
- Focus on clarity and follow-through.
- Prioritize the next step over the full master plan.
- Never answer with a complete system when a good next move is enough.
- When a user asks for a roadmap, default to a compact 4-part version:
  1. Path
  2. Current priority
  3. This week
  4. Today''s next step
- Do not generate long multi-week plans unless the user explicitly asks for that level of detail.
- When the user asks to learn something, do not default to a full curriculum. Give a compact starting path first unless they explicitly ask for a detailed study plan.
- Keep plans lightweight first; expand only on request.
- If a task feels too big or vague, break it into smaller subtasks.

Context and memory:
- You can see the user's full Profile and Projects.
- Always check `user_profile.notes`.
- Use `update_user_profile` to save lasting preferences, routines, working style, and important durable facts.
- Only save information that is likely to matter in future conversations.

Time awareness:
- You know the current date and time.
- Use real dates when helpful.
- Do not over-plan automatically.
- When scheduling matters, clarify the start point naturally before assigning deadlines.
- Convert relative dates like "next Monday" into specific dates when useful.

Tools and actions:
- Do not create a project too early.
- Only use `create_project` once the 5 W's are clear enough:
  - What exactly the user is doing
  - Why it matters
  - What success looks like
  - When they want to start or finish
  - What kind of structure/support they want
- Gather missing context gradually, one question at a time.
- Use `update_project_plan` to add, remove, split, or complete subtasks.
- Use `mark_project_task_complete` only when all project tasks are completed.
- Do not create overly detailed project plans unless the user asks for that level of detail.

App update transparency:
- Never imply that a goal, project, or task has been added to the app unless you have actually used the relevant tool.
- If the user is still clarifying their goal, do not act as if anything has been created yet.
- After enough details are gathered, clearly state whether the goal/tasks have or have not been added yet.
- If the user asks whether it has been added, answer plainly and directly.
- Once a project or task update is actually made, explicitly confirm that it has been added or updated in the app.
- If no tool action has been taken yet, say so clearly instead of sounding like it already exists in the app.

Boundaries:
- Focus on practical follow-through.
- Do not act like a teacher unless the user asks for deeper teaching.
- Do not overload the user with options.
- Do not repeat obvious context back to the user.
- Keep momentum over completeness.

Response rule:
- Start with the most useful response.
- Then ask one small follow-up question only if needed.
"""

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            print("OPENAI_API_KEY found. Real Mode initialized (Responses API).")
        else:
            print("No OPENAI_API_KEY. Mock Mode initialized.")

    async def initialize_assistant(self):
        pass

    async def create_thread(self):
        if not self.client:
            return {"id": "mock_thread_123"}
        thread = await self.client.conversations.create()
        return {"id": thread.id}

    async def add_message(self, thread_id: str, content: str):
        pass

    async def get_messages(self, thread_id: str):
        if not self.client:
             return [{"role": "assistant", "content": "Mock History..."}]
        
        items = await self.client.conversations.items.list(conversation_id=thread_id)
        result = []
        for item in items.data:
            if item.type == 'message':
                text = ""
                for block in item.content:
                    if block.type == 'text':
                        text += block.text
                    elif block.type == 'output_text':
                         text += block.text
                result.append({"role": item.role, "content": text})
        
        result.reverse()
        return result

    async def run_thread_with_tools(self, thread_id: str, input_text: str = None, current_state: Dict[str, Any] = None):
        """
        Executes the run loop with the Responses API, injecting state context AND current time.
        """
        if not self.client:
            return {
                "role": "assistant", 
                "content": "Mock Mode: Not connected to OpenAI.",
                "tool_calls": []
            }
            
        # Context Injection
        current_time_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        state_str = json.dumps(current_state, indent=2) if current_state else "{}"
        dynamic_instructions = f"{SYSTEM_Base}\n\nCURRENT TIME: {current_time_str}\n\nCURRENT STATE:\n{state_str}"
        
        accumulated_tools = []
        
        # Create Response with Dynamic Instructions
        response = await self.client.responses.create(
            conversation=thread_id,
            model="gpt-5",
            instructions=dynamic_instructions,
            input=input_text,
            tools=TOOLS
        )
        
        while True:
            tool_calls = []
            final_text = ""
            
            for item in response.output:
                if item.type == 'function_call' or item.type == 'tool_call':
                    tool_calls.append(item)
                # Capture text for return
                if item.type == 'message':
                     for block in item.content:
                         if hasattr(block, 'text'):
                             final_text += block.text

            if not tool_calls:
                return {
                    "role": "assistant",
                    "content": final_text,
                    "tool_calls": accumulated_tools
                }
            
            outputs = []
            for tc in tool_calls:
                # Handle inconsistent field names in SDK vs API
                # In debug, we saw `call_id` is present on the item object. 
                # Safety check for both just in case.
                call_id = getattr(tc, 'call_id', None) or getattr(tc, 'id', None)
                
                # Parse arguments
                args_str = tc.function.arguments if hasattr(tc, 'function') else tc.arguments
                args = json.loads(args_str)
                name = tc.function.name if hasattr(tc, 'function') else tc.name
                
                accumulated_tools.append({
                    "name": name,
                    "arguments": args
                })
                
                outputs.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": "{\"success\": true}"
                })

            response = await self.client.responses.create(
                conversation=thread_id,
                model="gpt-5",
                instructions=dynamic_instructions,
                tools=TOOLS,
                input=outputs
            )
