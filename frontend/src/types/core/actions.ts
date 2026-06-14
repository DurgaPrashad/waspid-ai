// Waspid AI OS
import { WaspidActionEvent } from "./base";
import { ActionSecurityRisk } from "#/stores/security-analyzer-store";

export interface UserMessageAction extends WaspidActionEvent<"message"> {
  source: "user";
  args: {
    content: string;
    image_urls: string[];
    file_urls: string[];
  };
}

export interface SystemMessageAction extends WaspidActionEvent<"system"> {
  source: "agent" | "environment";
  args: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    waspid_version: string | null;
    agent_class: string | null;
  };
}

export interface CommandAction extends WaspidActionEvent<"run"> {
  source: "agent" | "user";
  args: {
    command: string;
    security_risk: ActionSecurityRisk;
    confirmation_state: "confirmed" | "rejected" | "awaiting_confirmation";
    thought: string;
    hidden?: boolean;
  };
}

export interface AssistantMessageAction extends WaspidActionEvent<"message"> {
  source: "agent";
  args: {
    thought: string;
    image_urls: string[] | null;
    file_urls: string[];
    wait_for_response: boolean;
  };
}

export interface IPythonAction extends WaspidActionEvent<"run_ipython"> {
  source: "agent";
  args: {
    code: string;
    security_risk: ActionSecurityRisk;
    confirmation_state: "confirmed" | "rejected" | "awaiting_confirmation";
    kernel_init_code: string;
    thought: string;
  };
}

export interface ThinkAction extends WaspidActionEvent<"think"> {
  source: "agent";
  args: {
    thought: string;
  };
}

export interface FinishAction extends WaspidActionEvent<"finish"> {
  source: "agent";
  args: {
    final_thought: string;
    outputs: Record<string, unknown>;
    thought: string;
  };
}

export interface DelegateAction extends WaspidActionEvent<"delegate"> {
  source: "agent";
  timeout: number;
  args: {
    agent: "BrowsingAgent";
    inputs: Record<string, string>;
    thought: string;
  };
}

export interface BrowseAction extends WaspidActionEvent<"browse"> {
  source: "agent";
  args: {
    url: string;
    thought: string;
  };
}

export interface BrowseInteractiveAction extends WaspidActionEvent<"browse_interactive"> {
  source: "agent";
  timeout: number;
  args: {
    browser_actions: string;
    thought: string | null;
    browsergym_send_msg_to_user: string;
  };
}

export interface FileReadAction extends WaspidActionEvent<"read"> {
  source: "agent";
  args: {
    path: string;
    thought: string;
    security_risk: ActionSecurityRisk | null;
    impl_source?: string;
    view_range?: number[] | null;
  };
}

export interface FileWriteAction extends WaspidActionEvent<"write"> {
  source: "agent";
  args: {
    path: string;
    content: string;
    thought: string;
  };
}

export interface FileEditAction extends WaspidActionEvent<"edit"> {
  source: "agent";
  args: {
    path: string;
    command?: string;
    file_text?: string | null;
    view_range?: number[] | null;
    old_str?: string | null;
    new_str?: string | null;
    insert_line?: number | null;
    content?: string;
    start?: number;
    end?: number;
    thought: string;
    security_risk: ActionSecurityRisk | null;
    impl_source?: string;
  };
}

export interface RejectAction extends WaspidActionEvent<"reject"> {
  source: "agent";
  args: {
    thought: string;
  };
}

export interface RecallAction extends WaspidActionEvent<"recall"> {
  source: "agent";
  args: {
    recall_type: "workspace_context" | "knowledge";
    query: string;
    thought: string;
  };
}

export interface MCPAction extends WaspidActionEvent<"call_tool_mcp"> {
  source: "agent";
  args: {
    name: string;
    arguments: Record<string, unknown>;
    thought?: string;
  };
}

export interface TaskTrackingAction extends WaspidActionEvent<"task_tracking"> {
  source: "agent";
  args: {
    command: string;
    task_list: Array<{
      id: string;
      title: string;
      status: "todo" | "in_progress" | "done";
      notes?: string;
    }>;
    thought: string;
  };
}

export type WaspidAction =
  | UserMessageAction
  | AssistantMessageAction
  | SystemMessageAction
  | CommandAction
  | IPythonAction
  | ThinkAction
  | FinishAction
  | DelegateAction
  | BrowseAction
  | BrowseInteractiveAction
  | FileReadAction
  | FileEditAction
  | FileWriteAction
  | RejectAction
  | RecallAction
  | MCPAction
  | TaskTrackingAction;
