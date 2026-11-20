package com.goreecloud.projects.shared

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class ProjectSummary(val id: String, val name: String, val key: String)
data class IssueSummary(val id: String, val identifier: String, val title: String, val status: String)

@Composable
fun ProjectsOverview(
    projects: List<ProjectSummary>,
    selectedId: String?,
    onSelect: (ProjectSummary) -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(projects, key = { it.id }) { project ->
            ElevatedCard(onClick = { onSelect(project) }, modifier = Modifier.fillMaxWidth()) {
                Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(project.key, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                    Column {
                        Text(project.name, style = MaterialTheme.typography.titleMedium)
                        if (project.id == selectedId) Text("Selected", color = MaterialTheme.colorScheme.secondary, style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
    }
}

@Composable
fun IssueOverview(issues: List<IssueSummary>, modifier: Modifier = Modifier) {
    LazyColumn(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(issues, key = { it.id }) { issue ->
            OutlinedCard(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(issue.identifier, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary)
                    Text(issue.title, style = MaterialTheme.typography.bodyLarge)
                    Text(issue.status.replace('_', ' '), style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}
