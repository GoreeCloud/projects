package com.goreecloud.projects

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.goreecloud.projects.shared.IssueOverview
import com.goreecloud.projects.shared.IssueSummary
import com.goreecloud.projects.shared.ProjectSummary
import com.goreecloud.projects.shared.ProjectsOverview
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL

// Provisional GoreeCloud UI alpha semantic roles; the shared GC UI library remains the design authority.
// Material 3 is the outer Android theme; common Kotlin UI does not install another theme.
private val GoreeColors = lightColorScheme(
    primary = Color(0xFF5146C8), onPrimary = Color.White,
    primaryContainer = Color(0xFFE8E5FF), onPrimaryContainer = Color(0xFF30266F),
    background = Color(0xFFF6F7FB), surface = Color.White,
    onBackground = Color(0xFF1B2030), onSurface = Color(0xFF1B2030)
)

private class ProjectsApi(private val server: String, private val token: String) {
    init {
        val uri = URI(server)
        val safeDebug = BuildConfig.DEBUG && uri.scheme == "http" &&
            uri.host in listOf("10.0.2.2", "localhost", "127.0.0.1")
        require(uri.scheme == "https" || safeDebug) { "Use HTTPS, or local emulator HTTP in debug builds only" }
        require(!uri.host.isNullOrBlank() && uri.userInfo == null && uri.fragment == null) { "Invalid server URL" }
        require(token.length >= 24) { "Provide a valid API token" }
    }
    private suspend fun call(path: String, method: String = "GET", body: JSONObject? = null): String =
        withContext(Dispatchers.IO) {
            val connection = URL(server.trimEnd('/') + "/api/v1" + path).openConnection() as HttpURLConnection
            try {
                connection.requestMethod = method
                connection.connectTimeout = 8_000
                connection.readTimeout = 8_000
                connection.setRequestProperty("Authorization", "Bearer " + token)
                connection.setRequestProperty("Accept", "application/json")
                if (body != null) {
                    connection.doOutput = true
                    connection.setRequestProperty("Content-Type", "application/json")
                    connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                }
                val status = connection.responseCode
                if (status !in 200..299) throw IllegalStateException("Server returned HTTP " + status)
                connection.inputStream.bufferedReader().use { it.readText() }
            } finally {
                connection.disconnect()
            }
        }
    suspend fun projects(): List<ProjectSummary> {
        val raw = JSONArray(call("/projects"))
        return (0 until raw.length()).map { index ->
            val item = raw.getJSONObject(index)
            ProjectSummary(item.getString("id"), item.getString("name"), item.getString("project_key"))
        }
    }
    suspend fun issues(projectId: String): List<IssueSummary> {
        val raw = JSONArray(call("/projects/" + projectId + "/issues?limit=200"))
        return (0 until raw.length()).map { index ->
            val item = raw.getJSONObject(index)
            IssueSummary(item.getString("id"), item.getString("identifier"),
                item.getString("title"), item.getString("status"))
        }
    }
    suspend fun addIssue(projectId: String, title: String) {
        call("/projects/" + projectId + "/issues", "POST", JSONObject().put("title", title))
    }
    suspend fun addProject(name: String, key: String) {
        call("/projects", "POST", JSONObject().put("name", name).put("key", key))
    }
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme(colorScheme = GoreeColors) { ProjectsScreen() } }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ProjectsScreen() {
    val scope = rememberCoroutineScope()
    var server by remember { mutableStateOf("https://projects.example.invalid") }
    // Never persist or log secrets. In-memory credentials are lost when the app process ends.
    var token by remember { mutableStateOf("") }
    var connected by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var projects by remember { mutableStateOf(emptyList<ProjectSummary>()) }
    var issues by remember { mutableStateOf(emptyList<IssueSummary>()) }
    var selected by remember { mutableStateOf<ProjectSummary?>(null) }
    var newIssue by remember { mutableStateOf("") }
    var newProject by remember { mutableStateOf("") }
    var newKey by remember { mutableStateOf("") }

    fun runTask(block: suspend () -> Unit) {
        scope.launch {
            isLoading = true; error = ""
            try { block() } catch (ex: Exception) { error = ex.message ?: "Request failed" }
            finally { isLoading = false }
        }
    }
    fun api(): ProjectsApi = ProjectsApi(server.trim(), token)
    fun refresh() = runTask {
        val result = api().projects()
        projects = result
        connected = true
        selected = selected?.let { old -> result.find { it.id == old.id } } ?: result.firstOrNull()
        issues = selected?.let { api().issues(it.id) } ?: emptyList()
    }
    Scaffold(
        topBar = { CenterAlignedTopAppBar(title = { Text("GoreeCloud Projects") }) },
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (!connected) {
                Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Private project workspace", style = MaterialTheme.typography.headlineSmall)
                    Text("Connect to your self-hosted server. HTTPS is required outside local debug builds.")
                    OutlinedTextField(server, { server = it }, label = { Text("Server URL") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    OutlinedTextField(token, { token = it }, label = { Text("API access token") },
                        visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), singleLine = true)
                    Button(onClick = { refresh() }, enabled = !isLoading && token.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text("Connect") }
                }
            } else {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { refresh() }, enabled = !isLoading) { Text("Refresh") }
                    OutlinedButton(onClick = {
                        connected = false; token = ""; projects = emptyList(); issues = emptyList(); selected = null
                    }) { Text("Lock") }
                }
                Text("Projects", style = MaterialTheme.typography.titleLarge)
                ProjectsOverview(projects, selected?.id, onSelect = { project ->
                    selected = project
                    runTask { issues = api().issues(project.id) }
                }, modifier = Modifier.fillMaxWidth().weight(0.43f))
                Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    OutlinedTextField(newProject, { newProject = it }, label = { Text("Project name") }, modifier = Modifier.weight(1f), singleLine = true)
                    OutlinedTextField(newKey, { newKey = it }, label = { Text("Key") }, modifier = Modifier.weight(0.55f), singleLine = true)
                }
                OutlinedButton(enabled = !isLoading && newProject.isNotBlank() && newKey.isNotBlank(), onClick = {
                    runTask { api().addProject(newProject, newKey); newProject = ""; newKey = ""; projects = api().projects() }
                }) { Text("Add project") }
                Text(selected?.name?.let { "$it issues" } ?: "Select a project", style = MaterialTheme.typography.titleLarge)
                IssueOverview(issues, modifier = Modifier.fillMaxWidth().weight(0.57f))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(newIssue, { newIssue = it }, label = { Text("New issue") }, modifier = Modifier.weight(1f), singleLine = true)
                    Button(enabled = !isLoading && selected != null && newIssue.isNotBlank(), onClick = {
                        val id = selected?.id ?: return@Button
                        runTask { api().addIssue(id, newIssue); newIssue = ""; issues = api().issues(id) }
                    }) { Text("Add") }
                }
            }
            if (isLoading) LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            if (error.isNotEmpty()) Text(error, color = MaterialTheme.colorScheme.error)
        }
    }
}
