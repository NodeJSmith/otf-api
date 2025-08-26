#!/usr/bin/env python3
"""
AI-powered TypeScript code generator for Python model changes.
This script is called by the GitHub Actions workflow.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import subprocess


def main():
    """Main function to generate TypeScript updates."""
    print("🤖 Starting AI-powered TypeScript generation...")
    
    # Check for API key
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ CLAUDE_AUTO_SYNC_KEY not found in environment")
        print("💡 Make sure the GitHub secret is properly configured")
        sys.exit(1)
    
    # Install httpx if needed
    try:
        import httpx
    except ImportError:
        print("📦 Installing httpx...")
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
        import httpx
    
    # Generate change summary
    change_summary = generate_change_summary()
    
    # Read TypeScript context
    ts_context = read_typescript_context()
    
    # Call Claude API
    ai_response = call_claude_api(api_key, change_summary, ts_context)
    
    # Save and apply updates
    if ai_response:
        save_ai_response(ai_response)
        apply_typescript_updates(ai_response)
        print("✅ AI generation completed successfully")
    else:
        print("❌ AI generation failed")
        sys.exit(1)


def generate_change_summary() -> str:
    """Generate a summary of Python changes."""
    try:
        # Get changed files
        result = subprocess.run([
            'git', 'diff', '--name-only', 'HEAD~1', 'HEAD', '--', 'python/'
        ], capture_output=True, text=True, check=True)
        
        changed_files = [f for f in result.stdout.strip().split('\n') if f.strip()]
        
        # Get diff summary
        diff_result = subprocess.run([
            'git', 'diff', '--stat', 'HEAD~1', 'HEAD', '--', 'python/'
        ], capture_output=True, text=True, check=True)
        
        # Get key changes (first 100 lines)
        changes_result = subprocess.run([
            'git', 'diff', 'HEAD~1', 'HEAD', '--', 'python/'
        ], capture_output=True, text=True, check=True)
        
        summary = f"""# Python Changes Detected

## Files Changed
{chr(10).join(f"- {f}" for f in changed_files)}

## Diff Summary
{diff_result.stdout}

## Key Changes (first 100 lines)
{chr(10).join(changes_result.stdout.split(chr(10))[:100])}
"""
        
        # Save for later use
        Path('python_changes.md').write_text(summary)
        return summary
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating change summary: {e}")
        return "Error generating change summary"


def read_typescript_context() -> Dict[str, str]:
    """Read current TypeScript files for context."""
    ts_files = {}
    ts_dir = Path('typescript/src')
    
    if not ts_dir.exists():
        return {}
    
    key_patterns = ['api/*.ts', 'auth/*.ts', 'cache/*.ts', 'models.ts', 'otf.ts']
    
    for pattern in key_patterns:
        for file_path in ts_dir.glob(pattern):
            if file_path.is_file() and 'generated' not in str(file_path):
                rel_path = str(file_path.relative_to(ts_dir))
                try:
                    content = file_path.read_text()
                    # Truncate for API limits
                    if len(content) > 1500:
                        content = content[:1500] + f"\n... (truncated, {len(content)} total chars)"
                    ts_files[rel_path] = content
                except Exception as e:
                    ts_files[rel_path] = f"Error reading file: {e}"
    
    return ts_files


def call_claude_api(api_key: str, change_summary: str, ts_context: Dict[str, str]) -> Dict[str, Any]:
    """Call Claude API to generate TypeScript updates."""
    import httpx
    
    prompt = f"""You are a TypeScript expert updating an API client based on Python model changes.

## Python Changes:
{change_summary}

## Current TypeScript Implementation:
{json.dumps(ts_context, indent=2)}

## Task:
Analyze the Python changes and generate TypeScript implementation updates. Focus on:
1. API client methods that need updating for new/changed models
2. Data transformation logic changes  
3. Type exports in models.ts for new models
4. Cache implementations if model structures changed

Return JSON with this structure:
{{
  "summary": "Brief description of what changed and why updates are needed",
  "files": {{
    "relative/path.ts": {{
      "action": "update", 
      "changes": "Description of specific changes made",
      "content": "Complete updated file content"
    }}
  }},
  "breaking_changes": ["list any breaking changes"],
  "notes": "Additional notes for human reviewer"
}}

Only include files that actually need changes. Keep existing patterns and style."""
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022", 
                    "max_tokens": 4000,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["content"][0]["text"]
                
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    try:
                        ai_json = json.loads(json_match.group())
                        print(f"✅ AI generation successful")
                        print(f"Summary: {ai_json.get('summary', 'No summary')}")
                        print(f"Files to update: {len(ai_json.get('files', {}))}")
                        return ai_json
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parse error: {e}")
                        print(f"Raw response: {ai_response[:500]}")
                        return {}
                else:
                    print("❌ No JSON found in AI response")
                    print(f"Raw response: {ai_response[:500]}")
                    return {}
            else:
                print(f"❌ Claude API error: {response.status_code}")
                print(response.text[:500])
                return {}
                
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return {}


def save_ai_response(ai_response: Dict[str, Any]) -> None:
    """Save AI response to file."""
    Path('ai_updates.json').write_text(json.dumps(ai_response, indent=2))


def apply_typescript_updates(ai_response: Dict[str, Any]) -> None:
    """Apply AI-generated updates to TypeScript files."""
    ts_src = Path('typescript/src')
    files_updated = 0
    
    for file_path, update_info in ai_response.get('files', {}).items():
        if update_info.get('action') == 'update':
            full_path = ts_src / file_path
            
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write updated content
            try:
                full_path.write_text(update_info['content'])
                print(f"✅ Updated {file_path}")
                files_updated += 1
            except Exception as e:
                print(f"❌ Failed to update {file_path}: {e}")
    
    print(f"📊 Total files updated: {files_updated}")


if __name__ == "__main__":
    main()