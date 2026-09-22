import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  AlertTriangle,
  ClipboardCheck,
  Clock3,
  Columns2,
  Download,
  FileText,
  FlaskConical,
  Gauge,
  Menu,
  Play,
  Plus,
  RefreshCw,
  Scale,
  Target,
  Trash2,
  X
} from 'lucide-react';
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { REPORT_DOWNLOAD_BASE, apiDelete, apiGet, apiPost } from './api/client';
import './index.css';

type DashboardMetrics = {
  targets: number;
  audits: number;
  audits_running: number;
  findings: number;
  critical_findings: number;
  highest_disparity: number;
  low_signal_findings: number;
  findings_by_attribute: { attribute: string; findings: number; max_disparity: number; probes: number }[];
  findings_by_severity: Record<string, number>;
  recent_audits: { id: string; name: string; status: string; created_at: string }[];
};

type TargetRead = {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  description: string | null;
  provider: string;
  model_name: string;
  configuration: Record<string, unknown>;
};

type AuditRead = {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  description: string | null;
  target_id: string;
  probe_ids: string[];
  evaluator_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
};

type ProbeRead = {
  id: string;
  name: string;
  description: string;
  attribute: string;
  groups: string[];
  jurisdiction: string;
  source: string;
  legal_basis: string;
};

type EvaluatorRead = {
  id: string;
  name: string;
  description: string;
  metric: string;
};

type FindingRead = {
  id: string;
  audit_id: string;
  probe_id: string;
  probe_name: string;
  attribute: string;
  evaluator_id: string;
  metric: string;
  severity: string;
  disparity_score: number;
  confidence: number;
  arm_count: number;
  low_signal: boolean;
  summary: string;
  metrics: Record<string, number>;
  evidence: Record<string, unknown>;
  created_at: string;
};

type ProbeResultRead = {
  id: string;
  audit_id: string;
  probe_id: string;
  attribute: string;
  prompts: Record<string, string>;
  responses: Record<string, string>;
  errors: Record<string, string>;
  created_at: string;
};

type ReportRead = {
  id: string;
  audit_id: string;
  format: string;
  content: string;
  created_at: string;
};

type AuditRunResponse = {
  audit_id: string;
  status: string;
  probes_run: number;
  findings: number;
  highest_disparity: number;
};

type ProbeRunResponse = {
  probe_id: string;
  attribute: string;
  prompts: Record<string, string>;
  responses: Record<string, string>;
  evaluation: Record<string, unknown>;
};

const queryClient = new QueryClient();

const emptyMetrics: DashboardMetrics = {
  targets: 0,
  audits: 0,
  audits_running: 0,
  findings: 0,
  critical_findings: 0,
  low_signal_findings: 0,
  highest_disparity: 0,
  findings_by_attribute: [],
  findings_by_severity: {},
  recent_audits: []
};

const tabs = [
  ['Overview', Gauge],
  ['Targets', Target],
  ['Audits', ClipboardCheck],
  ['Probes', FlaskConical],
  ['Findings', AlertTriangle],
  ['Reports', FileText]
] as const;

function App() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number][0]>('Overview');
  const [mobileOpen, setMobileOpen] = useState(false);
  const metrics = useQuery({ queryKey: ['dashboard'], queryFn: () => apiGet<DashboardMetrics>('/dashboard'), retry: false });
  const targets = useQuery({ queryKey: ['targets'], queryFn: () => apiGet<TargetRead[]>('/targets'), retry: false });
  const audits = useQuery({ queryKey: ['audits'], queryFn: () => apiGet<AuditRead[]>('/audits'), retry: false });
  const probes = useQuery({ queryKey: ['probes'], queryFn: () => apiGet<ProbeRead[]>('/probes'), retry: false });
  const evaluators = useQuery({ queryKey: ['evaluators'], queryFn: () => apiGet<EvaluatorRead[]>('/evaluators'), retry: false });
  const queries = [metrics, targets, audits, probes, evaluators];
  const isLoading = queries.some((query) => query.isLoading);
  const firstError = queries.find((query) => query.error)?.error;

  const nav = (
    <nav className="mt-8 space-y-1">
      {tabs.map(([label, Icon]) => (
        <button
          key={label}
          onClick={() => {
            setActiveTab(label);
            setMobileOpen(false);
          }}
          className={`flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-sm ${activeTab === label ? 'bg-panel font-medium text-ink' : 'text-slate-600 hover:bg-panel hover:text-ink'}`}
        >
          <Icon size={18} /> {label}
        </button>
      ))}
    </nav>
  );

  return (
    <main className="min-h-screen bg-[#eef1f5] text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
        <Brand />
        {nav}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-20 bg-black/30 lg:hidden" onClick={() => setMobileOpen(false)}>
          <aside className="h-full w-72 border-r border-line bg-white px-4 py-5" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between">
              <Brand />
              <IconButton label="Close menu" onClick={() => setMobileOpen(false)}><X size={18} /></IconButton>
            </div>
            {nav}
          </aside>
        </div>
      )}
      <section className="lg:pl-64">
        <header className="sticky top-0 z-10 flex min-h-16 items-center justify-between border-b border-line bg-white px-4 py-3 lg:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <IconButton label="Open menu" className="lg:hidden" onClick={() => setMobileOpen(true)}><Menu size={18} /></IconButton>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold lg:text-xl">Fairness Evaluation Dashboard</h1>
              <p className="truncate text-sm text-slate-600">Targets, audits, probes, findings, and reports</p>
            </div>
          </div>
          <button onClick={() => queryClient.invalidateQueries()} className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm hover:bg-panel">
            <RefreshCw size={16} /> <span className="hidden sm:inline">Refresh</span>
          </button>
        </header>
        <div className="p-4 lg:p-5">
          {isLoading && <Banner tone="info" text="Loading workspace data..." />}
          {firstError && <Banner tone="danger" text={messageFor(firstError, 'Unable to load dashboard data.')} />}
          {activeTab === 'Overview' && <Overview values={metrics.data ?? emptyMetrics} audits={audits.data ?? []} targets={targets.data ?? []} />}
          {activeTab === 'Targets' && <Targets targets={targets.data ?? []} />}
          {activeTab === 'Audits' && <Audits audits={audits.data ?? []} targets={targets.data ?? []} probes={probes.data ?? []} evaluators={evaluators.data ?? []} />}
          {activeTab === 'Probes' && <Probes probes={probes.data ?? []} targets={targets.data ?? []} />}
          {activeTab === 'Findings' && <Findings audits={audits.data ?? []} />}
          {activeTab === 'Reports' && <Reports audits={audits.data ?? []} />}
        </div>
      </section>
    </main>
  );
}

function Overview({ values, audits, targets }: { values: DashboardMetrics; audits: AuditRead[]; targets: TargetRead[] }) {
  const severities = ['critical', 'high', 'medium', 'low', 'info'];
  return (
    <div className="space-y-5">
      <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric label="Targets" value={values.targets} />
        <Metric label="Audits" value={values.audits} />
        <Metric label="Running" value={values.audits_running} />
        <Metric label="Findings" value={values.findings} />
        <Metric label="Critical" value={values.critical_findings} danger />
        <Metric label="Low signal" value={values.low_signal_findings} />
        <Metric label="Max disparity" value={values.highest_disparity.toFixed(3)} />
      </section>
      <div className="grid gap-5 xl:grid-cols-[1.3fr_1fr]">
        <Panel title="Disparity By Protected Attribute" empty={values.findings_by_attribute.length === 0} emptyText="No findings yet. Run an audit to populate this.">
          {values.findings_by_attribute.map((row) => (
            <div key={row.attribute} className="border-b border-line px-4 py-3 text-sm last:border-b-0">
              <div className="flex items-center justify-between">
                <span className="font-medium">{row.attribute}</span>
                <span className="text-slate-600">{row.findings} finding(s) across {row.probes} probe(s) &middot; max {row.max_disparity.toFixed(3)}</span>
              </div>
              <DisparityBar value={row.max_disparity} />
            </div>
          ))}
          <p className="px-4 py-3 text-xs text-slate-500">
            Bars show the single highest score for each attribute, so an attribute covered by more probes
            has more chances to produce a high one. Read the bar next to the probe count, not on its own —
            this is not a ranking of how biased the model is per attribute.
          </p>
        </Panel>
        <div className="space-y-5">
          <Panel title="Findings By Severity" empty={Object.keys(values.findings_by_severity).length === 0} emptyText="No findings yet.">
            {severities
              .filter((severity) => values.findings_by_severity[severity])
              .map((severity) => (
                <Row key={severity} title={severity} meta={`${values.findings_by_severity[severity]} finding(s)`} badge={severity} />
              ))}
          </Panel>
          <Panel title="Recent Audits" empty={audits.length === 0} emptyText="No audits yet.">
            {audits.slice(0, 5).map((audit) => (
              <Row key={audit.id} title={audit.name} meta={`${statusLabel(audit.status)} / ${targetName(targets, audit.target_id)}`} badge={audit.status} />
            ))}
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Targets({ targets }: { targets: TargetRead[] }) {
  const client = useQueryClient();
  const [form, setForm] = useState({ name: '', description: '', provider: 'mock', modelName: 'mock-model', baseUrl: '', apiKey: '', mockMode: 'noisy' });
  const [error, setError] = useState('');

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    const configuration: Record<string, unknown> = {};
    if (form.baseUrl) configuration.base_url = form.baseUrl;
    if (form.apiKey) configuration.api_key = form.apiKey;
    if (form.provider === 'mock') configuration.mode = form.mockMode;
    try {
      await apiPost<TargetRead>('/targets', {
        name: form.name,
        description: form.description || null,
        provider: form.provider,
        model_name: form.modelName,
        configuration
      });
      setForm({ ...form, name: '', description: '', apiKey: '' });
      await client.invalidateQueries();
    } catch (err) {
      setError(messageFor(err, 'Unable to save target'));
    }
  }

  async function remove(id: string) {
    await apiDelete(`/targets/${id}`);
    await client.invalidateQueries();
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <FormShell title="Add Target" error={error} onSubmit={submit} submitLabel="Save Target">
        <Field label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} required />
        <Field label="Description" value={form.description} onChange={(description) => setForm({ ...form, description })} />
        <Select
          label="Provider"
          value={form.provider}
          onChange={(provider) => setForm({ ...form, provider })}
          options={[
            ['mock', 'Built-in mock (offline)'],
            ['google_gemini', 'Google Gemini'],
            ['openai', 'OpenAI'],
            ['openai_compatible', 'OpenAI-compatible (Ollama, vLLM)'],
            ['anthropic', 'Anthropic']
          ]}
        />
        <Field label="Model" value={form.modelName} onChange={(modelName) => setForm({ ...form, modelName })} required />
        {form.provider === 'mock' && (
          <>
            <Select
              label="Mock mode"
              value={form.mockMode}
              onChange={(mockMode) => setForm({ ...form, mockMode })}
              options={[
                ['noisy', 'Noisy - hash-seeded variation (default)'],
                ['fair', 'Fair - identical reply to every arm'],
                ['biased', 'Biased - degraded reply for planted groups'],
                ['refusing', 'Refusing - declines for planted groups']
              ]}
            />
            <p className="mt-2 text-xs text-slate-600">
              Calibration modes plant known ground truth. <strong>Fair</strong> must produce zero findings;
              <strong> biased</strong> must produce findings on the planted group and nowhere else. They test
              the instrument, not any model.
            </p>
          </>
        )}
        <Field label="Base URL" value={form.baseUrl} onChange={(baseUrl) => setForm({ ...form, baseUrl })} placeholder="http://host.docker.internal:11434/v1" />
        <Field label="API Key" value={form.apiKey} onChange={(apiKey) => setForm({ ...form, apiKey })} type="password" />
        <p className="mt-3 text-xs text-slate-600">
          The mock provider needs no key. Inside Docker, a model running on your own machine is reached at
          <code className="mx-1 rounded bg-panel px-1">host.docker.internal</code>, not <code className="rounded bg-panel px-1">localhost</code>.
        </p>
      </FormShell>
      <Panel title="Targets" empty={targets.length === 0} emptyText="No targets yet.">
        {targets.map((target) => (
          <Row
            key={target.id}
            title={target.name}
            meta={`${target.provider} / ${target.model_name}${target.description ? ` / ${target.description}` : ''}`}
            action={<IconButton label="Delete target" onClick={() => remove(target.id)}><Trash2 size={16} /></IconButton>}
          />
        ))}
      </Panel>
    </div>
  );
}

function Audits({ audits, targets, probes, evaluators }: { audits: AuditRead[]; targets: TargetRead[]; probes: ProbeRead[]; evaluators: EvaluatorRead[] }) {
  const client = useQueryClient();
  const [form, setForm] = useState({ name: '', targetId: '', evaluatorId: 'composite-disparity', probeIds: [] as string[] });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [lastRun, setLastRun] = useState<AuditRunResponse | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    try {
      await apiPost<AuditRead>('/audits', {
        name: form.name,
        target_id: form.targetId || targets[0]?.id,
        probe_ids: form.probeIds,
        evaluator_id: form.evaluatorId
      });
      setForm({ ...form, name: '', probeIds: [] });
      await client.invalidateQueries();
    } catch (err) {
      setError(messageFor(err, 'Unable to create audit'));
    }
  }

  async function run(id: string) {
    setError('');
    setBusy(id);
    try {
      setLastRun(await apiPost<AuditRunResponse>(`/audits/${id}/run`));
      await client.invalidateQueries();
    } catch (err) {
      setError(messageFor(err, 'Audit run failed'));
    } finally {
      setBusy('');
    }
  }

  async function remove(id: string) {
    await apiDelete(`/audits/${id}`);
    await client.invalidateQueries();
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <FormShell title="New Audit" error={error} onSubmit={submit} submitLabel="Create Audit" disabled={targets.length === 0}>
        <Field label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} required />
        <Select label="Target" value={form.targetId} onChange={(targetId) => setForm({ ...form, targetId })} options={targets.map((target) => [target.id, target.name])} required />
        <Select label="Evaluator" value={form.evaluatorId} onChange={(evaluatorId) => setForm({ ...form, evaluatorId })} options={evaluators.map((evaluator) => [evaluator.id, evaluator.name])} />
        <Checklist title="Probes (leave empty to run all)" probes={probes} selected={form.probeIds} onChange={(probeIds) => setForm({ ...form, probeIds })} />
        {targets.length === 0 && <p className="mt-3 text-sm text-danger">Add a target first.</p>}
      </FormShell>
      <div className="space-y-5">
        {lastRun && (
          <Banner
            tone="info"
            text={`Audit finished: ${lastRun.probes_run} probes run, ${lastRun.findings} finding(s), highest disparity ${lastRun.highest_disparity.toFixed(3)}.`}
          />
        )}
        <Panel title="Audits" empty={audits.length === 0} emptyText="No audits yet.">
          {audits.map((audit) => (
            <Row
              key={audit.id}
              title={audit.name}
              meta={`${targetName(targets, audit.target_id)} / ${audit.probe_ids.length} probes / ${audit.evaluator_id}${audit.error ? ` / ${audit.error}` : ''}`}
              badge={audit.status}
              action={
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => run(audit.id)}
                    disabled={busy === audit.id}
                    className="inline-flex h-9 items-center gap-2 rounded-md bg-ink px-3 text-sm font-medium text-white disabled:opacity-50"
                  >
                    <Play size={15} /> {busy === audit.id ? 'Running...' : 'Run'}
                  </button>
                  <IconButton label="Delete audit" onClick={() => remove(audit.id)}><Trash2 size={16} /></IconButton>
                </div>
              }
            />
          ))}
        </Panel>
      </div>
    </div>
  );
}

function Probes({ probes, targets }: { probes: ProbeRead[]; targets: TargetRead[] }) {
  const [form, setForm] = useState({ probeId: '', targetId: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ProbeRunResponse | null>(null);
  const attributes = Array.from(new Set(probes.map((probe) => probe.attribute)));
  const [jurisdiction, setJurisdiction] = useState('all');
  const visible = probes.filter(
    (probe) => jurisdiction === 'all' || probe.jurisdiction === jurisdiction || probe.jurisdiction === 'cross'
  );

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    const target = targets.find((item) => item.id === form.targetId) ?? targets[0];
    try {
      setResult(
        await apiPost<ProbeRunResponse>(`/probes/${form.probeId || probes[0]?.id}/run`, {
          target_id: target?.id ?? null,
          provider: target?.provider ?? 'mock',
          model_name: target?.model_name ?? 'mock-model',
          configuration: target?.configuration ?? {}
        })
      );
    } catch (err) {
      setError(messageFor(err, 'Probe run failed'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <FormShell title="Run One Probe" error={error} onSubmit={submit} submitLabel={busy ? 'Running...' : 'Run Probe'} submitIcon={<Play size={16} />} disabled={busy || probes.length === 0}>
        <Select label="Probe" value={form.probeId} onChange={(probeId) => setForm({ ...form, probeId })} options={probes.map((probe) => [probe.id, probe.name])} />
        <Select label="Target" value={form.targetId} onChange={(targetId) => setForm({ ...form, targetId })} options={targets.map((target) => [target.id, target.name])} />
        <p className="mt-3 text-xs text-slate-600">Runs a single probe without creating an audit. Nothing is stored - useful while developing new probes.</p>
      </FormShell>
      <div className="space-y-5">
        <Panel title={`Probe Library (${visible.length} probes, ${attributes.length} attributes)`} empty={visible.length === 0} emptyText="No probes registered.">
          <div className="flex flex-wrap gap-2 border-b border-line px-4 py-3">
            {[['all', 'All jurisdictions'], ['us', 'United States'], ['eu', 'European Union']].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setJurisdiction(value)}
                className={`rounded-full px-3 py-1 text-xs font-medium ${jurisdiction === value ? 'bg-accent text-white' : 'bg-slate-100 text-slate-700'}`}
              >
                {label}
              </button>
            ))}
            <span className="self-center text-xs text-slate-500">Jurisdiction-neutral probes appear under every filter.</span>
          </div>
          {visible.map((probe) => (
            <Row
              key={probe.id}
              title={probe.name}
              meta={`${probe.description} Groups: ${probe.groups.join(', ')} | Names: ${probe.source} | Legal basis: ${probe.legal_basis}`}
              badge={`${probe.attribute} \u00b7 ${probe.jurisdiction}`}
            />
          ))}
        </Panel>
        {result && (
          <Panel title="Probe Result" empty={false} emptyText="">
            <Comparison prompts={result.prompts} responses={result.responses} metrics={(result.evaluation.group_metrics as Record<string, number>) ?? {}} />
            <JsonBlock value={result.evaluation} />
          </Panel>
        )}
      </div>
    </div>
  );
}

function Findings({ audits }: { audits: AuditRead[] }) {
  const completed = audits.filter((audit) => audit.status === 'completed');
  const [auditId, setAuditId] = useState('');
  const selected = auditId || completed[0]?.id || '';
  const [openId, setOpenId] = useState('');

  const findings = useQuery({
    queryKey: ['findings', selected],
    queryFn: () => apiGet<FindingRead[]>(`/audits/${selected}/findings`),
    enabled: Boolean(selected),
    retry: false
  });
  const results = useQuery({
    queryKey: ['results', selected],
    queryFn: () => apiGet<ProbeResultRead[]>(`/audits/${selected}/results`),
    enabled: Boolean(selected),
    retry: false
  });

  if (completed.length === 0) return <Banner tone="info" text="No completed audit yet. Create an audit and run it first." />;

  const rows = findings.data ?? [];
  const evidence = results.data ?? [];

  return (
    <div className="space-y-5">
      <section className="rounded-md border border-line bg-white p-4">
        <Select label="Audit" value={selected} onChange={setAuditId} options={completed.map((audit) => [audit.id, audit.name])} />
      </section>
      <Panel title={`Findings (${rows.length})`} empty={rows.length === 0} emptyText="No disparity above the warning threshold was measured.">
        {rows.map((finding) => {
          const probeResult = evidence.find((item) => item.probe_id === finding.probe_id);
          const open = openId === finding.id;
          return (
            <div key={finding.id} className="border-b border-line last:border-b-0">
              <div className="flex flex-col gap-3 px-4 py-3 text-sm md:flex-row md:items-center md:justify-between">
                <div className="min-w-0">
                  <div className="truncate font-medium">{finding.probe_name || finding.probe_id}</div>
                  <div className="break-words text-slate-600">{finding.summary}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    metric <code className="rounded bg-panel px-1">{finding.metric || 'n/a'}</code> &middot; confidence {finding.confidence} &middot; {finding.arm_count} arms
                  </div>
                  {finding.low_signal && (
                    <div className="mt-1 text-xs text-amber-700">
                      Low signal - the responses were short enough that wording alone can move this score. Read the comparison before trusting it.
                    </div>
                  )}
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{finding.attribute}</span>
                  <SeverityBadge value={finding.severity} />
                  <span className="w-16 text-right font-semibold">{finding.disparity_score.toFixed(3)}</span>
                  <button
                    onClick={() => setOpenId(open ? '' : finding.id)}
                    className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm hover:bg-panel"
                  >
                    <Columns2 size={15} /> {open ? 'Hide' : 'Compare'}
                  </button>
                </div>
              </div>
              <div className="px-4 pb-3"><DisparityBar value={finding.disparity_score} /></div>
              {open && probeResult && (
                <div className="border-t border-line bg-panel/40">
                  <Comparison prompts={probeResult.prompts} responses={probeResult.responses} metrics={finding.metrics} />
                </div>
              )}
              {open && !probeResult && <div className="px-4 pb-4 text-sm text-slate-600">Raw responses for this probe are no longer stored.</div>}
            </div>
          );
        })}
      </Panel>
    </div>
  );
}

function Comparison({ prompts, responses, metrics }: { prompts: Record<string, string>; responses: Record<string, string>; metrics: Record<string, number> }) {
  const groups = Object.keys(responses);
  return (
    <div className="overflow-x-auto p-4">
      <div className="flex gap-4">
        {groups.map((group) => (
          <article key={group} className="w-80 shrink-0 rounded-md border border-line bg-white">
            <header className="flex items-center justify-between border-b border-line px-3 py-2">
              <span className="text-sm font-semibold">{group}</span>
              {metrics[group] !== undefined && <span className="text-xs text-slate-600">{Number(metrics[group]).toFixed(3)}</span>}
            </header>
            <div className="border-b border-line px-3 py-2 text-xs text-slate-600">{prompts[group]}</div>
            <div className="whitespace-pre-wrap px-3 py-2 text-sm">{responses[group] || '(empty response)'}</div>
          </article>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-600">
        These prompts are identical apart from the protected attribute. Any systematic difference between the columns is what the disparity score measures.
      </p>
    </div>
  );
}

function Reports({ audits }: { audits: AuditRead[] }) {
  const client = useQueryClient();
  const completed = audits.filter((audit) => audit.status === 'completed');
  const [form, setForm] = useState({ auditId: '', format: 'markdown' });
  const [error, setError] = useState('');
  const reports = useQuery({ queryKey: ['reports'], queryFn: () => apiGet<ReportRead[]>('/reports'), retry: false });

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    try {
      await apiPost<ReportRead>('/reports', { audit_id: form.auditId || completed[0]?.id, format: form.format });
      await client.invalidateQueries();
    } catch (err) {
      setError(messageFor(err, 'Unable to generate report'));
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <FormShell title="Generate Report" error={error} onSubmit={submit} submitLabel="Generate" disabled={completed.length === 0}>
        <Select label="Audit" value={form.auditId} onChange={(auditId) => setForm({ ...form, auditId })} options={completed.map((audit) => [audit.id, audit.name])} />
        <Select label="Format" value={form.format} onChange={(format) => setForm({ ...form, format })} options={[['markdown', 'Markdown'], ['html', 'HTML'], ['json', 'JSON']]} />
        {completed.length === 0 && <p className="mt-3 text-sm text-danger">Run an audit first.</p>}
      </FormShell>
      <Panel title="Reports" empty={(reports.data ?? []).length === 0} emptyText="No reports yet.">
        {(reports.data ?? []).map((report) => (
          <Row
            key={report.id}
            title={auditName(audits, report.audit_id)}
            meta={`${report.format} / ${formatDate(report.created_at)}`}
            action={
              <a
                href={`${REPORT_DOWNLOAD_BASE}/reports/${report.id}/download`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm hover:bg-panel"
              >
                <Download size={15} /> Open
              </a>
            }
          />
        ))}
      </Panel>
    </div>
  );
}

function Brand() {
  return <div className="flex items-center gap-2 text-lg font-semibold"><Scale size={22} /> Bias Auditor</div>;
}

function FormShell({ title, error, onSubmit, submitLabel, submitIcon, disabled, children }: { title: string; error: string; onSubmit: (event: React.FormEvent) => void; submitLabel: string; submitIcon?: React.ReactNode; disabled?: boolean; children: React.ReactNode }) {
  return (
    <form onSubmit={onSubmit} className="rounded-md border border-line bg-white p-4">
      <h2 className="font-semibold">{title}</h2>
      {children}
      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
      <button disabled={disabled} className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-ink px-3 text-sm font-medium text-white disabled:opacity-50">
        {submitIcon ?? <Plus size={16} />} {submitLabel}
      </button>
    </form>
  );
}

function Metric({ label, value, danger = false }: { label: string; value: number | string; danger?: boolean }) {
  return <div className="rounded-md border border-line bg-white p-4"><div className="text-sm text-slate-600">{label}</div><div className={danger ? 'mt-2 text-2xl font-semibold text-danger' : 'mt-2 text-2xl font-semibold'}>{value}</div></div>;
}

function DisparityBar({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, value * 100));
  const tone = value >= 0.35 ? 'bg-danger' : value >= 0.25 ? 'bg-warn' : 'bg-accent';
  return (
    <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100">
      <div className={`h-1.5 rounded-full ${tone}`} style={{ width: `${percent}%` }} />
    </div>
  );
}

function Field({ label, value, onChange, required = false, type = 'text', placeholder = '' }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string; placeholder?: string }) {
  return <label className="mt-3 block text-sm text-slate-600">{label}<input type={type} value={value} onChange={(event) => onChange(event.target.value)} required={required} placeholder={placeholder} className="mt-1 h-10 w-full rounded-md border border-line px-3 text-sm text-ink outline-none focus:border-accent" /></label>;
}

function Select({ label, value, onChange, options, required = false }: { label: string; value: string; onChange: (value: string) => void; options: string[][]; required?: boolean }) {
  return (
    <label className="mt-3 block text-sm text-slate-600">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} required={required} className="mt-1 h-10 w-full rounded-md border border-line px-3 text-sm text-ink outline-none focus:border-accent">
        {options.length === 0 && <option value="">None available</option>}
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  );
}

function Checklist({ title, probes, selected, onChange }: { title: string; probes: ProbeRead[]; selected: string[]; onChange: (ids: string[]) => void }) {
  return (
    <>
      <div className="mt-3 text-sm text-slate-600">{title}</div>
      <div className="mt-2 max-h-56 space-y-2 overflow-auto rounded-md border border-line p-2">
        {probes.length === 0 && <div className="px-2 py-3 text-sm text-slate-600">No probes available.</div>}
        {probes.map((probe) => (
          <label key={probe.id} className="flex gap-2 text-sm">
            <input type="checkbox" checked={selected.includes(probe.id)} onChange={(event) => onChange(event.target.checked ? [...selected, probe.id] : selected.filter((id) => id !== probe.id))} />
            <span>{probe.name}</span>
          </label>
        ))}
      </div>
    </>
  );
}

function Panel({ title, empty, emptyText, children }: { title: string; empty: boolean; emptyText: string; children: React.ReactNode }) {
  return <section className="rounded-md border border-line bg-white"><div className="border-b border-line px-4 py-3"><h2 className="font-semibold">{title}</h2></div>{empty ? <div className="px-4 py-6 text-sm text-slate-600">{emptyText}</div> : children}</section>;
}

function Row({ title, meta, badge, action }: { title: string; meta: string; badge?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 border-b border-line px-4 py-3 text-sm last:border-b-0 md:flex-row md:items-center md:justify-between">
      <div className="min-w-0">
        <div className="truncate font-medium">{title}</div>
        <div className="break-words text-slate-600">{meta}</div>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        {badge && <SeverityBadge value={badge} />}
        {action}
      </div>
    </div>
  );
}

function SeverityBadge({ value }: { value: string }) {
  const severe = ['critical', 'high', 'failed'].includes(value);
  const medium = ['medium', 'running', 'pending'].includes(value);
  const tone = severe ? 'bg-red-50 text-danger' : medium ? 'bg-amber-50 text-warn' : 'bg-slate-100 text-slate-700';
  return <span className={`rounded-full px-2 py-1 text-xs font-medium ${tone}`}>{statusLabel(value)}</span>;
}

function IconButton({ label, onClick, className = '', children }: { label: string; onClick: () => void; className?: string; children: React.ReactNode }) {
  return <button type="button" title={label} aria-label={label} onClick={onClick} className={`inline-flex h-9 w-9 items-center justify-center rounded-md border border-line hover:bg-panel ${className}`}>{children}</button>;
}

function Banner({ tone, text }: { tone: 'info' | 'danger'; text: string }) {
  return <div className={`mb-4 flex items-center gap-2 rounded-md border px-4 py-3 text-sm ${tone === 'danger' ? 'border-red-200 bg-red-50 text-danger' : 'border-line bg-white text-slate-600'}`}>{tone === 'danger' ? <AlertCircle size={16} /> : <Clock3 size={16} />}{text}</div>;
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="max-h-80 overflow-auto border-t border-line px-4 py-3 text-xs">{JSON.stringify(value, null, 2)}</pre>;
}

function targetName(targets: TargetRead[], id: string) {
  return targets.find((target) => target.id === id)?.name ?? 'Unknown target';
}

function auditName(audits: AuditRead[], id: string) {
  return audits.find((audit) => audit.id === id)?.name ?? 'Unknown audit';
}

function statusLabel(value: string) {
  return value.replace(/_/g, ' ');
}

function formatDate(value: string | null) {
  if (!value) return 'unknown';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

function messageFor(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

createRoot(document.getElementById('root')!).render(<QueryClientProvider client={queryClient}><App /></QueryClientProvider>);
