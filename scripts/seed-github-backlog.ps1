<#
Seeds the GitHub backlog: labels, release milestones, 10 epic issues and 73 story
issues linked to their epic.

Source of truth for acceptance criteria stays in _bmad-output/planning-artifacts/epics.md.
Issues carry the user story, the FR references and a link back to the doc, so the two
never drift.

Safe to re-run: existing labels and milestones are reused, and issues are only created
when no open issue with the same title exists.

    pwsh -File scripts/seed-github-backlog.ps1
    pwsh -File scripts/seed-github-backlog.ps1 -WhatIf   # show what would be created
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Repo = "laxmikantp38/jarvis",
    [switch]$WithProject
)

$ErrorActionPreference = "Stop"

# gh is installed machine-wide; a stale shell may not have picked it up yet.
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

function Test-Auth {
    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not authenticated. Run: gh auth login" -ForegroundColor Red
        exit 1
    }
}

$DocBase = "https://github.com/$Repo/blob/main/_bmad-output/planning-artifacts/epics.md"

# --- labels ------------------------------------------------------------------
$Labels = @(
    @{ name = "epic";        color = "5319E7"; desc = "Epic - a group of stories delivering one outcome" }
    @{ name = "story";       color = "0E8A16"; desc = "Story - completable in a single focused session" }
    @{ name = "outline";     color = "C5DEF5"; desc = "Acceptance criteria not yet written - expanded at its release" }
    @{ name = "R1";          color = "B60205"; desc = "Release 1 - survive and measure (build now)" }
    @{ name = "R2";          color = "D93F0B"; desc = "Release 2 - leverage (month 7+)" }
    @{ name = "R3";          color = "FBCA04"; desc = "Release 3 - judgement and reach" }
    @{ name = "R4";          color = "BFDADC"; desc = "Release 4 - the office floor" }
    @{ name = "blocked-ext"; color = "000000"; desc = "Blocked on external lead time (e.g. WhatsApp BSP verification)" }
)

# --- milestones --------------------------------------------------------------
$Milestones = @(
    @{ title = "R1 - Survive and measure"; desc = "Epics 1-3. The system wakes him, remembers his work, and reports weekly whether the revenue target is still reachable. Roughly two months." }
    @{ title = "R2 - Leverage";            desc = "Epics 4-6. Planning, execution and voice. Resumes in month 7 with four months of real usage behind the decisions." }
    @{ title = "R3 - Judgement and reach"; desc = "Epics 7-9. Advice layer, remote reach, content pipeline." }
    @{ title = "R4 - The office floor";    desc = "Epic 10. The isometric office as the full agent surface." }
)

# --- epics and their stories -------------------------------------------------
# title | release | fr coverage | anchor | stories( id | title | detailed? )
$Epics = @(
    @{
        n = 1; title = "It wakes me up"; release = "R1"; milestone = "R1 - Survive and measure"
        goal = "Nudges fire on my real routine from a service that starts itself on boot and survives reboot without a login. Usable on its own."
        frs = "FR-25 to FR-32, FR-30 (Telegram), FR-54 (footage warning), FR-93 to FR-97"
        anchor = "#epic-1-it-wakes-me-up"
        detailed = $true
        stories = @(
            "1.1|Start on boot and say hello|the system to start itself whenever my machine starts and greet me|I never have to remember to launch it and I know immediately that it is alive"
            "1.2|Keep configuration and secrets out of the code|configuration and credentials handled properly from the first commit|I can rename the assistant, swap a model provider or rotate a token without touching source"
            "1.3|Schedule my routine|my fixed daily routine held as real scheduled triggers|the system knows when my day happens without me re-explaining it"
            "1.4|Reach me on Telegram|nudges delivered to Telegram and to be able to reply|the system reaches me on a phone I already carry, and I can answer it"
            "1.5|Don't spam me|the system to respect my attention|I keep reading its messages instead of muting it"
            "1.6|Tell me what you missed|to know when the system was down and what it missed|I can trust its silence instead of wondering whether it broke"
            "1.7|Warn me before tonight's reel has no footage|to be told during the day when tonight's upload has nothing behind it|I find out at 10:00 while I can still act, not at 23:10 when I cannot"
        )
    }
    @{
        n = 2; title = "It knows my work"; release = "R1"; milestone = "R1 - Survive and measure"
        goal = "I message the system on Telegram and it understands and remembers - routine, projects, tasks, stable facts. State survives restart and restore is proven."
        frs = "FR-42, FR-43, FR-44, FR-73, FR-74, FR-75, FR-87"
        anchor = "#epic-2-it-knows-my-work"
        detailed = $true
        stories = @(
            "2.1|Remember who I am and how my week runs|the system to hold my routine and working style as structured data|everything it later plans or suggests is built on how my week actually works"
            "2.2|Capture a task from a message|to send a message and have it become a tracked task|things stop living in my head while I am away from a desk"
            "2.3|Organise my work into projects|my work grouped into the ventures I actually run|the system can later reason about them separately"
            "2.4|Ask it what I've got on|to ask questions in natural language and get grounded answers|I can check state from my phone without opening anything"
            "2.5|Keep client work off hosted models|confidential work provably excluded from third-party models|using this system cannot breach my client obligations"
            "2.6|Survive a restart, and prove I can restore|my data durable and my backups actually tested|months of accumulated context cannot vanish"
            "2.7|See it in a browser|a local web interface with honest empty states|I have somewhere to look that tells me the truth on day one"
        )
    }
    @{
        n = 3; title = "It follows the money"; release = "R1"; milestone = "R1 - Survive and measure"
        goal = "Log an earning or expense in seconds; see required pace, trajectory, gap and net; get told early when the numbers stop adding up."
        frs = "FR-6 to FR-11, FR-80 to FR-86, FR-98 to FR-104"
        anchor = "#epic-3-it-follows-the-money"
        detailed = $true
        stories = @(
            "3.1|Log an earning in seconds|to record money received in a few words|logging never becomes the thing I stop doing"
            "3.2|Log an expense the same way|expenses captured at the same low friction|I see net rather than only gross"
            "3.3|Set any goal, not just a money one|the goal engine to hold any kind of target|the system is not welded to one number I might abandon"
            "3.4|See required pace and where I actually am|the arithmetic of my target computed honestly|I know the gap rather than guessing it"
            "3.5|Tell me when it doesn't add up|to be told early and plainly when my target is out of reach|I can change strategy while there is still time"
            "3.6|Show me net, not just gross|gross, expenses and net side by side, and profitability per venture|I can see which projects actually make money"
            "3.7|Propose the split once there's evidence|the system to derive my goal split from where money actually arrives|my targets stop being guesses"
        )
    }
    @{
        n = 4; title = "It tells me what to do next"; release = "R2"; milestone = "R2 - Leverage"
        goal = "A realistic daily plan that respects fixed commitments and leaves buffer, and one answer with reasoning whenever asked."
        frs = "FR-1, FR-2, FR-12 to FR-24"
        anchor = "#epic-4-it-tells-me-what-to-do-next"
        detailed = $false
        stories = @(
            "4.1|Score every task against my goals"
            "4.2|Sort my backlog into do-now, this-week, scheduled and delete"
            "4.3|Build me a realistic day"
            "4.4|Protect the time that never gets protected"
            "4.5|Ask what to do right now"
            "4.6|Tell me when I'm about to waste an evening"
            "4.7|Replan when the day breaks"
            "4.8|Explain any ranking"
        )
    }
    @{
        n = 5; title = "It does work when I ask"; release = "R2"; milestone = "R2 - Leverage"
        goal = "Executes approved work through GitHub, files, browser and research - nothing above a safe local draft without approval, everything audited."
        frs = "FR-34 to FR-41, FR-45, FR-76 to FR-79, FR-90 to FR-92"
        anchor = "#epic-5-it-does-work-when-i-ask"
        detailed = $false
        stories = @(
            "5.1|Refuse anything not in the registry"
            "5.2|Ask before you act"
            "5.3|Approve from wherever I am"
            "5.4|Never act twice"
            "5.5|Read my repositories"
            "5.6|Draft and file, but don't push"
            "5.7|Work with my files and the web"
            "5.8|Treat what you read as data, not orders"
            "5.9|Tell me the truth when it fails"
            "5.10|Show me everything you did and who approved it"
            "5.11|Show me who's working"
            "5.12|Know what's wrong with Railzy"
        )
    }
    @{
        n = 6; title = "I can use it in the car"; release = "R2"; milestone = "R2 - Leverage"
        goal = "Spoken commute briefing; create, reschedule and ask by voice without touching a screen."
        frs = "FR-57 to FR-62"
        anchor = "#epic-6-i-can-use-it-in-the-car"
        detailed = $false
        stories = @(
            "6.1|Talk to me on the drive"
            "6.2|Brief me before I arrive"
            "6.3|Change my plan by voice"
            "6.4|Know where I am"
            "6.5|Never make me look at a screen mid-drive"
        )
    }
    @{
        n = 7; title = "It advises me"; release = "R3"; milestone = "R3 - Judgement and reach"
        goal = "Recommendations with evidence, a decision journal that answers why we decided things, experiments that conclude, and a weekly review ending in exactly three focus items."
        frs = "FR-3, FR-4, FR-5, FR-46 to FR-50, FR-63 to FR-72"
        anchor = "#epic-7-it-advises-me"
        detailed = $false
        stories = @(
            "7.1|Show your working"
            "7.2|Disagree with me when the data supports it"
            "7.3|Remember why we decided things"
            "7.4|Tell me when a past decision has expired"
            "7.5|Run experiments that actually conclude"
            "7.6|Learn how wrong my estimates are"
            "7.7|Brief me each morning and review each night"
            "7.8|Give me three things a week, not twenty"
            "7.9|Call out what I keep avoiding"
            "7.10|Show me where my time actually went"
        )
    }
    @{
        n = 8; title = "It reaches me anywhere"; release = "R3"; milestone = "R3 - Judgement and reach"
        goal = "WhatsApp nudges, a ringing wake-up call, and a phone view of the latest encrypted screen capture with command entry."
        frs = "FR-30 (WhatsApp), FR-33"
        anchor = "#epic-8-it-reaches-me-anywhere"
        detailed = $false
        blocked = $true
        stories = @(
            "8.1|Nudge me on WhatsApp"
            "8.2|Actually wake me up"
            "8.3|Put a courier on a server that can't do anything"
            "8.4|Let me see my screen from my phone"
            "8.5|Command it from anywhere"
        )
    }
    @{
        n = 9; title = "The reel ships itself"; release = "R3"; milestone = "R3 - Judgement and reach"
        goal = "Content calendar, per-platform generation, and shipping reduced to a single approval."
        frs = "FR-51, FR-52, FR-53, FR-55, FR-56"
        anchor = "#epic-9-the-reel-ships-itself"
        detailed = $false
        stories = @(
            "9.1|Track every piece of content through its lifecycle"
            "9.2|Show me the calendar and what's missing"
            "9.3|Draft titles, hooks, descriptions, tags and captions per platform"
            "9.4|Reduce shipping to one approval"
            "9.5|Learn what actually performs"
        )
    }
    @{
        n = 10; title = "The office floor"; release = "R4"; milestone = "R4 - The office floor"
        goal = "The isometric office as the full agent surface - cabins, orchestrator, owner's corner office, approvals arriving at the desk."
        frs = "FR-88, FR-89"
        anchor = "#epic-10-the-office-floor"
        detailed = $false
        stories = @(
            "10.1|Build the isometric floor"
            "10.2|Give every role a recognisable person"
            "10.3|Make assignment visible"
            "10.4|Make approvals arrive at my desk"
            "10.5|Light the room"
            "10.6|Handle a real floor, not a demo"
            "10.7|Stay cheap enough to leave open all day"
        )
    }
)

# --- run ---------------------------------------------------------------------
Test-Auth
Write-Host "Repo: $Repo" -ForegroundColor Cyan

Write-Host "`nLabels..." -ForegroundColor Cyan
foreach ($l in $Labels) {
    if ($PSCmdlet.ShouldProcess($l.name, "create label")) {
        gh label create $l.name --repo $Repo --color $l.color --description $l.desc --force 2>&1 | Out-Null
        Write-Host "  $($l.name)"
    }
}

Write-Host "`nMilestones..." -ForegroundColor Cyan
$existing = gh api "repos/$Repo/milestones?state=all" --jq '.[].title' 2>$null
foreach ($m in $Milestones) {
    if ($existing -contains $m.title) { Write-Host "  $($m.title) (exists)"; continue }
    if ($PSCmdlet.ShouldProcess($m.title, "create milestone")) {
        gh api "repos/$Repo/milestones" -f title="$($m.title)" -f description="$($m.desc)" 2>&1 | Out-Null
        Write-Host "  $($m.title)"
    }
}

function Get-IssueNumber([string]$Title) {
    $found = gh issue list --repo $Repo --state all --search "`"$Title`" in:title" --json number,title --limit 50 2>$null |
             ConvertFrom-Json | Where-Object { $_.title -eq $Title } | Select-Object -First 1
    if ($found) { return $found.number }
    return $null
}

Write-Host "`nEpics and stories..." -ForegroundColor Cyan
$created = 0; $skipped = 0

foreach ($e in $Epics) {
    $epicTitle = "Epic $($e.n): $($e.title)"
    $epicNum = Get-IssueNumber $epicTitle

    if (-not $epicNum) {
        $body = @"
$($e.goal)

**Release:** $($e.release)
**Requirements covered:** $($e.frs)

Full epic detail, stories and acceptance criteria live in the planning doc:
$DocBase$($e.anchor)

Stories are tracked as separate issues and reference this one.
"@
        if ($PSCmdlet.ShouldProcess($epicTitle, "create epic issue")) {
            $labels = "epic,$($e.release)"
            if ($e.blocked) { $labels += ",blocked-ext" }
            $url = gh issue create --repo $Repo --title $epicTitle --body $body `
                     --label $labels --milestone $e.milestone 2>&1 | Select-Object -Last 1
            $epicNum = ($url -split '/')[-1]
            Write-Host "  [$epicNum] $epicTitle" -ForegroundColor Green
            $created++
        }
    } else {
        Write-Host "  [$epicNum] $epicTitle (exists)" -ForegroundColor DarkGray
        $skipped++
    }

    foreach ($s in $e.stories) {
        $parts = $s -split '\|'
        $id = $parts[0]; $name = $parts[1]
        $storyTitle = "Story ${id}: $name"
        if (Get-IssueNumber $storyTitle) { $skipped++; continue }

        if ($e.detailed) {
            $storyBody = @"
As the owner,
I want $($parts[2]),
so that $($parts[3]).

**Epic:** #$epicNum - $($e.title)
**Release:** $($e.release)

Acceptance criteria are in the planning doc (search for ``Story $id``):
$DocBase$($e.anchor)

Definition of done also requires the architecture invariants in ``ARCHITECTURE-SPINE.md``
that this story touches - a story that violates an AD is not done.
"@
            $labels = "story,$($e.release)"
        } else {
            $storyBody = @"
**Epic:** #$epicNum - $($e.title)
**Release:** $($e.release)

Outline only. Acceptance criteria are written when $($e.release) begins - detailing work
this far out, against a system whose real usage will reshape it, is waste.

$DocBase$($e.anchor)
"@
            $labels = "story,outline,$($e.release)"
        }
        if ($e.blocked) { $labels += ",blocked-ext" }

        if ($PSCmdlet.ShouldProcess($storyTitle, "create story issue")) {
            gh issue create --repo $Repo --title $storyTitle --body $storyBody `
                --label $labels --milestone $e.milestone 2>&1 | Out-Null
            Write-Host "    $storyTitle"
            $created++
        }
    }
}

Write-Host "`nCreated $created, skipped $skipped." -ForegroundColor Cyan

if ($WithProject) {
    Write-Host "`nProject board..." -ForegroundColor Cyan
    gh project list --owner "@me" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Needs the project scope. Run: gh auth refresh -s project,read:project" -ForegroundColor Yellow
    } else {
        gh project create --owner "@me" --title "Jarvis Build" 2>&1 | Out-String | Write-Host
        Write-Host "  Add issues to the board from the project UI, or re-run with the project number." -ForegroundColor Yellow
    }
}

Write-Host "`nBoard: https://github.com/$Repo/issues" -ForegroundColor Green
Write-Host "Start here: Story 1.1" -ForegroundColor Green
