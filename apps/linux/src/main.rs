//! GoreeCloud Projects Linux client.
//! Native Slint UI. Network requests execute on workers, never the UI thread.
use serde::Deserialize;
use serde_json::json;
use slint::{ModelRc, VecModel};
use std::{env, rc::Rc, thread, time::Duration};

slint::slint! {
    import { Button, LineEdit, VerticalBox, HorizontalBox, ScrollView } from "std-widgets.slint";
    export struct ProjectRow { id: string, name: string, key: string }
    export struct IssueRow { name: string, status: string }
    export component ProjectsWindow inherits Window {
        title: "GoreeCloud Projects";
        width: 930px;
        height: 700px;
        background: #F6F7FB;
        in-out property <string> server_url: "http://127.0.0.1:8000";
        in-out property <string> status_text: "Connect with PROJECTS_ADMIN_TOKEN in your environment";
        in-out property <[ProjectRow]> projects;
        in-out property <[IssueRow]> issues;
        in-out property <string> selected_id: "";
        in-out property <string> selected_title: "Select a project";
        in-out property <string> issue_title: "";
        in-out property <string> new_project_name: "";
        in-out property <string> new_project_key: "";
        callback refresh();
        callback select_project(string, string);
        callback create_project();
        callback create_issue();
        VerticalLayout {
            padding: 24px;
            spacing: 13px;
            Text { text: "GoreeCloud Projects"; color: #1B2030; font-size: 31px; font-weight: 700; }
            Text { text: "Native Linux workspace · development preview"; color: #505B70; font-size: 13px; }
            HorizontalLayout {
                spacing: 10px;
                Text { text: "Server"; color: #505B70; vertical-alignment: center; }
                LineEdit { text <=> root.server_url; }
                Button { text: "Refresh"; clicked => { root.refresh(); } }
            }
            Rectangle { background: #E8E5FF; border-radius: 12px; height: 42px;
                Text { text: root.status_text; color: #30266F; x: 12px; vertical-alignment: center; }
            }
            HorizontalLayout {
                spacing: 15px;
                VerticalLayout {
                    spacing: 9px;
                    min-width: 275px;
                    max-width: 315px;
                    Text { text: "Projects"; color: #1B2030; font-size: 20px; font-weight: 600; }
                    ScrollView {
                        VerticalLayout {
                            spacing: 5px;
                            for p in root.projects: Button {
                                text: p.key + " · " + p.name;
                                clicked => { root.select_project(p.id, p.name); }
                            }
                        }
                    }
                    Text { text: "New project"; font-weight: 600; color: #1B2030; }
                    LineEdit { text <=> root.new_project_name; placeholder-text: "Project name"; }
                    LineEdit { text <=> root.new_project_key; placeholder-text: "Key (e.g. NOTE)"; }
                    Button { text: "Create project"; clicked => { root.create_project(); } }
                }
                VerticalLayout {
                    spacing: 9px;
                    Text { text: root.selected_title; color: #1B2030; font-size: 20px; font-weight: 600; }
                    ScrollView {
                        VerticalLayout {
                            spacing: 5px;
                            for issue in root.issues : Rectangle {
                                height: 45px;
                                background: #FFFFFF;
                                border-radius: 10px;
                                HorizontalLayout {
                                    padding: 10px;
                                    spacing: 13px;
                                    Text { text: issue.name; color: #1B2030; horizontal-stretch: 1; }
                                    Text { text: issue.status; color: #505B70; font-size: 12px; }
                                }
                            }
                        }
                    }
                    Text { text: "New issue"; font-weight: 600; color: #1B2030; }
                    LineEdit { text <=> root.issue_title; placeholder-text: "Describe the work"; }
                    Button { text: "Create issue"; clicked => { root.create_issue(); } }
                }
            }
        }
    }
}
#[derive(Deserialize)]
struct Project {
    id: String,
    name: String,
    project_key: String,
}
#[derive(Deserialize)]
struct Issue {
    identifier: String,
    title: String,
    status: String,
}
fn call_get<T: serde::de::DeserializeOwned>(base: &str, path: &str, token: &str) -> Result<T, String> {
    let response = ureq::get(&format!("{}{}", base.trim_end_matches('/'), path))
        .set("Authorization", &format!("Bearer {token}"))
        .timeout(Duration::from_secs(8)).call().map_err(|e| e.to_string())?;
    response.into_json().map_err(|e| e.to_string())
}
fn call_post(base: &str, path: &str, token: &str, body: serde_json::Value) -> Result<(), String> {
    ureq::post(&format!("{}{}", base.trim_end_matches('/'), path))
        .set("Authorization", &format!("Bearer {token}"))
        .timeout(Duration::from_secs(8)).send_json(body)
        .map_err(|e| e.to_string())?;
    Ok(())
}
fn update_status(weak: slint::Weak<ProjectsWindow>, result: Result<String, String>) {
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(ui) = weak.upgrade() {
            ui.set_status_text(result.unwrap_or_else(|e| format!("Request failed: {e}")).into());
        }
    });
}
fn load_issues(weak: slint::Weak<ProjectsWindow>, base: String, token: String, id: String) {
    thread::spawn(move || {
        let response = call_get::<Vec<Issue>>(&base, &format!("/api/v1/projects/{id}/issues"), &token);
        match response {
            Ok(issues) => {
                let data = issues.into_iter().map(|issue| IssueRow {
                    name: format!("{} · {}", issue.identifier, issue.title).into(),
                    status: issue.status.into(),
                }).collect::<Vec<_>>();
                let _ = slint::invoke_from_event_loop(move || {
                    if let Some(ui) = weak.upgrade() {
                        ui.set_issues(ModelRc::from(Rc::new(VecModel::from(data))));
                        ui.set_status_text("Issues synchronized".into());
                    }
                });
            }
            Err(err) => update_status(weak, Err(err)),
        }
    });
}
fn main() -> Result<(), slint::PlatformError> {
    let ui = ProjectsWindow::new()?;
    if let Ok(url) = env::var("GOREECLOUD_PROJECTS_API_URL") { ui.set_server_url(url.into()); }
    let token = env::var("PROJECTS_ADMIN_TOKEN").unwrap_or_default();
    {
        let weak = ui.as_weak();
        let token = token.clone();
        ui.on_refresh(move || {
            let Some(ui) = weak.upgrade() else {return};
            let base = ui.get_server_url().to_string();
            let weak = weak.clone();
            let token = token.clone();
            thread::spawn(move || {
                if token.len() < 24 { update_status(weak, Err("Set a random PROJECTS_ADMIN_TOKEN with 24+ characters".into())); return; }
                match call_get::<Vec<Project>>(&base, "/api/v1/projects", &token) {
                    Ok(projects) => {
                        let rows = projects.into_iter().map(|p| ProjectRow {
                            id: p.id.into(), name: p.name.into(), key: p.project_key.into(),
                        }).collect::<Vec<_>>();
                        let _ = slint::invoke_from_event_loop(move || {
                            if let Some(ui) = weak.upgrade() {
                                ui.set_projects(ModelRc::from(Rc::new(VecModel::from(rows))));
                                ui.set_status_text("Projects synchronized".into());
                            }
                        });
                    },
                    Err(e) => update_status(weak, Err(e)),
                }
            });
        });
    }
    {
        let weak = ui.as_weak();
        let token = token.clone();
        ui.on_select_project(move |id, name| {
            let Some(ui) = weak.upgrade() else {return};
            ui.set_selected_id(id.clone());
            ui.set_selected_title(name);
            load_issues(weak.clone(), ui.get_server_url().to_string(), token.clone(), id.to_string());
        });
    }
    {
        let weak = ui.as_weak();
        let token = token.clone();
        ui.on_create_project(move || {
            let Some(ui) = weak.upgrade() else {return};
            let name = ui.get_new_project_name().to_string();
            let key = ui.get_new_project_key().to_string();
            if name.trim().is_empty() || key.trim().is_empty() { ui.set_status_text("Enter project name and key".into());return; }
            let base = ui.get_server_url().to_string();
            let weak = weak.clone();
            let token = token.clone();
            thread::spawn(move || {
                let result = call_post(&base, "/api/v1/projects", &token, json!({"name": name, "key": key}));
                let _ = slint::invoke_from_event_loop(move || {
                    if let Some(ui) = weak.upgrade() {
                        match result { Ok(()) => {ui.set_status_text("Project created — refresh to see it".into());ui.set_new_project_name("".into());ui.set_new_project_key("".into());},
                                       Err(e) => ui.set_status_text(format!("Request failed: {e}").into()) }
                    }
                });
            });
        });
    }
    {
        let weak = ui.as_weak();
        ui.on_create_issue(move || {
            let Some(ui) = weak.upgrade() else {return};
            let id = ui.get_selected_id().to_string();
            let title = ui.get_issue_title().to_string();
            if id.is_empty() || title.trim().is_empty() {ui.set_status_text("Choose a project and enter issue title".into());return;}
            let base = ui.get_server_url().to_string();
            let weak = weak.clone();
            let token = token.clone();
            thread::spawn(move || {
                match call_post(&base, &format!("/api/v1/projects/{id}/issues"), &token, json!({"title": title})) {
                    Ok(()) => {
                        let _ = slint::invoke_from_event_loop({
                            let weak = weak.clone();
                            move || { if let Some(ui)=weak.upgrade(){ ui.set_issue_title("".into()); } }
                        });
                        load_issues(weak, base, token, id);
                    }
                    Err(e) => update_status(weak, Err(e)),
                }
            });
        });
    }
    ui.run()
}
