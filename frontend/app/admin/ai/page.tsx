'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { useConfirm } from '@/components/admin/ConfirmDialog'
import { useToast } from '@/components/admin/Toast'
import { api } from '@/lib/api'
import {
  AI_PROVIDER_LABELS,
  AI_SUPPORTED_PROVIDERS,
  type AIProvider,
  type AIProviderSettings,
} from '@/lib/types'

const PROVIDERS: AIProvider[] = ['gemini', 'openai', 'claude', 'openai_compatible']

// 只是表單預填的建議值，欄位本身可自由編輯——各家 provider 的可用
// model 名稱變動很快（例如 Gemini 免費方案已知會不定期調整哪些
// model 開放），這裡不保證永遠是當下最新、最適合的選擇。
const DEFAULT_MODEL: Record<AIProvider, string> = {
  gemini: 'gemini-3.6-flash',
  openai: 'gpt-4o-mini',
  claude: 'claude-3-5-haiku-20241022',
  openai_compatible: '',
}

function isSupported(provider: AIProvider) {
  return AI_SUPPORTED_PROVIDERS.includes(provider)
}

interface EditState {
  model: string
  base_url: string
  api_key: string
  remove_api_key: boolean
  timeout_seconds: string
  max_output_tokens: string
  top_k: string
}

function toEditState(s: AIProviderSettings): EditState {
  return {
    model: s.model,
    base_url: s.base_url ?? '',
    api_key: '',
    remove_api_key: false,
    timeout_seconds: String(s.timeout_seconds),
    max_output_tokens: String(s.max_output_tokens),
    top_k: String(s.top_k),
  }
}

export default function AISettingsPage() {
  const confirm = useConfirm()
  const toast = useToast()

  const [list, setList] = useState<AIProviderSettings[]>([])
  const [loading, setLoading] = useState(true)

  const [provider, setProvider] = useState<AIProvider>('gemini')
  const [model, setModel] = useState(DEFAULT_MODEL.gemini)
  const [baseUrl, setBaseUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [creating, setCreating] = useState(false)

  const [editId, setEditId] = useState<number | null>(null)
  const [edit, setEdit] = useState<EditState | null>(null)
  const [savingEdit, setSavingEdit] = useState(false)

  const [busyId, setBusyId] = useState<number | null>(null)
  const [testResults, setTestResults] = useState<Record<number, string>>({})

  function refresh() {
    return api.listAISettings().then(setList)
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [])

  function handleProviderChange(p: AIProvider) {
    setProvider(p)
    setModel(DEFAULT_MODEL[p])
    if (p !== 'openai_compatible') setBaseUrl('')
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!model.trim()) return
    if (provider === 'openai_compatible' && !baseUrl.trim()) {
      toast.error('OpenAI 相容服務必須填寫 Base URL')
      return
    }
    setCreating(true)
    try {
      await api.createAISettings({
        provider,
        model: model.trim(),
        base_url: provider === 'openai_compatible' ? baseUrl.trim() : null,
        api_key: apiKey.trim() || null,
      })
      await refresh()
      setModel(DEFAULT_MODEL[provider])
      setBaseUrl('')
      setApiKey('')
      toast.success('已新增 provider 設定')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '新增失敗')
    } finally {
      setCreating(false)
    }
  }

  function startEdit(s: AIProviderSettings) {
    setEditId(s.id)
    setEdit(toEditState(s))
  }

  async function handleSaveEdit(s: AIProviderSettings) {
    if (!edit) return
    setSavingEdit(true)
    try {
      await api.updateAISettings(s.id, {
        model: edit.model.trim(),
        base_url: s.provider === 'openai_compatible' ? edit.base_url.trim() : null,
        api_key: edit.api_key.trim() || undefined,
        remove_api_key: edit.remove_api_key,
        timeout_seconds: Number(edit.timeout_seconds) || undefined,
        max_output_tokens: Number(edit.max_output_tokens) || undefined,
        top_k: Number(edit.top_k) || undefined,
      })
      await refresh()
      setEditId(null)
      setEdit(null)
      toast.success('已儲存變更')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '儲存失敗')
    } finally {
      setSavingEdit(false)
    }
  }

  async function handleToggleEnabled(s: AIProviderSettings) {
    setBusyId(s.id)
    try {
      if (s.is_enabled) {
        await api.disableAISettings(s.id)
        toast.success('已停用')
      } else {
        await api.enableAISettings(s.id)
        toast.success(`已啟用 ${AI_PROVIDER_LABELS[s.provider]}，其餘 provider 會自動停用`)
      }
      await refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '操作失敗')
    } finally {
      setBusyId(null)
    }
  }

  async function handleTest(s: AIProviderSettings) {
    setBusyId(s.id)
    try {
      const result = await api.testAISettings(s.id)
      setTestResults(prev => ({
        ...prev,
        [s.id]: result.success
          ? `連線成功（延遲 ${Math.round(result.latency_ms ?? 0)}ms）`
          : `連線失敗：${result.error_category ?? '未知錯誤'}`,
      }))
      if (result.success) toast.success('測試連線成功')
      else toast.error('測試連線失敗')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '測試連線失敗')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(s: AIProviderSettings) {
    const ok = await confirm({
      title: '刪除 provider 設定',
      message: `確定要刪除「${AI_PROVIDER_LABELS[s.provider]} / ${s.model}」這筆設定嗎？此操作無法復原。`,
      confirmLabel: '刪除',
      danger: true,
    })
    if (!ok) return
    setBusyId(s.id)
    try {
      await api.deleteAISettings(s.id)
      await refresh()
      toast.success('已刪除')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '刪除失敗')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <AdminShell title="AI 助理設定">
      <p className="text-sm text-sumi-light mb-6 max-w-xl leading-relaxed">
        設定 AI 助理使用的模型服務商。同一時間只能啟用一個 provider，啟用新的會自動停用舊的。
        Gemini、OpenAI、Claude 都使用官方 endpoint，只有 OpenAI 相容服務可以自訂 Base
        URL（例如本機的 Ollama）；正式環境預設拒絕 Base URL 指向內網或 loopback 位址。
      </p>

      <form onSubmit={handleCreate} className="border border-hairline rounded p-5 mb-8 bg-white max-w-xl">
        <p className="text-xs text-sumi-light uppercase tracking-widest mb-4">新增 Provider 設定</p>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ai-new-provider" className="text-xs text-sumi-light">Provider</label>
            <select
              id="ai-new-provider"
              name="provider"
              value={provider}
              onChange={e => handleProviderChange(e.target.value as AIProvider)}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai bg-white"
            >
              {PROVIDERS.map(p => (
                <option key={p} value={p}>
                  {AI_PROVIDER_LABELS[p]}
                  {!isSupported(p) ? '（尚未支援啟用）' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="ai-new-model" className="text-xs text-sumi-light">Model *</label>
            <input
              id="ai-new-model"
              name="model"
              type="text"
              required
              value={model}
              onChange={e => setModel(e.target.value)}
              className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
            />
          </div>

          {provider === 'openai_compatible' && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ai-new-base-url" className="text-xs text-sumi-light">Base URL *</label>
              <input
                id="ai-new-base-url"
                name="base_url"
                type="text"
                required
                value={baseUrl}
                onChange={e => setBaseUrl(e.target.value)}
                placeholder="http://host.docker.internal:11434/v1"
                className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label htmlFor="ai-new-api-key" className="text-xs text-sumi-light">API Key</label>
            <input
              id="ai-new-api-key"
              name="api_key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="留白代表稍後再補上"
              className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
            />
          </div>

          <button
            type="submit"
            disabled={creating}
            className="self-start text-sm bg-sumi text-washi px-4 py-2 rounded hover:bg-ai transition-colors disabled:opacity-50"
          >
            {creating ? '新增中…' : '新增設定'}
          </button>
        </div>
      </form>

      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : list.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無 provider 設定，用上方表單新增。</p>
      ) : (
        <div className="flex flex-col gap-4 max-w-xl">
          {list.map(s => {
            const supported = isSupported(s.provider)
            const isEditing = editId === s.id
            return (
              <div key={s.id} className="border border-hairline rounded p-5 bg-white">
                {isEditing && edit ? (
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-2 text-sm text-sumi">
                      <span className="font-medium">{AI_PROVIDER_LABELS[s.provider]}</span>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor={`edit-model-${s.id}`} className="text-xs text-sumi-light">Model</label>
                      <input
                        id={`edit-model-${s.id}`}
                        value={edit.model}
                        onChange={e => setEdit({ ...edit, model: e.target.value })}
                        className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
                      />
                    </div>
                    {s.provider === 'openai_compatible' && (
                      <div className="flex flex-col gap-1.5">
                        <label htmlFor={`edit-base-url-${s.id}`} className="text-xs text-sumi-light">Base URL</label>
                        <input
                          id={`edit-base-url-${s.id}`}
                          value={edit.base_url}
                          onChange={e => setEdit({ ...edit, base_url: e.target.value })}
                          className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
                        />
                      </div>
                    )}
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor={`edit-api-key-${s.id}`} className="text-xs text-sumi-light">
                        更換 API Key（留白代表保留原本的 key）
                      </label>
                      <input
                        id={`edit-api-key-${s.id}`}
                        type="password"
                        autoComplete="off"
                        value={edit.api_key}
                        onChange={e => setEdit({ ...edit, api_key: e.target.value, remove_api_key: false })}
                        className="border border-hairline rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-ai"
                      />
                    </div>
                    {s.is_configured && (
                      <label className="flex items-center gap-2 text-xs text-sumi-light">
                        <input
                          type="checkbox"
                          checked={edit.remove_api_key}
                          onChange={e => setEdit({ ...edit, remove_api_key: e.target.checked, api_key: '' })}
                        />
                        移除目前已存的 API key
                      </label>
                    )}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="flex flex-col gap-1.5">
                        <label htmlFor={`edit-timeout-${s.id}`} className="text-xs text-sumi-light">Timeout（秒）</label>
                        <input
                          id={`edit-timeout-${s.id}`}
                          type="number"
                          min={1}
                          value={edit.timeout_seconds}
                          onChange={e => setEdit({ ...edit, timeout_seconds: e.target.value })}
                          className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai"
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label htmlFor={`edit-max-tokens-${s.id}`} className="text-xs text-sumi-light">最大輸出 token</label>
                        <input
                          id={`edit-max-tokens-${s.id}`}
                          type="number"
                          min={1}
                          value={edit.max_output_tokens}
                          onChange={e => setEdit({ ...edit, max_output_tokens: e.target.value })}
                          className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai"
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label htmlFor={`edit-top-k-${s.id}`} className="text-xs text-sumi-light">top_k</label>
                        <input
                          id={`edit-top-k-${s.id}`}
                          type="number"
                          min={1}
                          value={edit.top_k}
                          onChange={e => setEdit({ ...edit, top_k: e.target.value })}
                          className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai"
                        />
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleSaveEdit(s)}
                        disabled={savingEdit}
                        className="text-sm bg-ai text-white px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50"
                      >
                        {savingEdit ? '儲存中…' : '儲存'}
                      </button>
                      <button
                        onClick={() => { setEditId(null); setEdit(null) }}
                        className="text-sm text-sumi-light hover:text-sumi transition-colors"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm text-sumi font-medium">
                          {AI_PROVIDER_LABELS[s.provider]}
                          <span className="text-sumi-light font-normal"> / {s.model}</span>
                        </p>
                        {s.provider === 'openai_compatible' && s.base_url && (
                          <p className="text-xs text-sumi-light font-mono mt-0.5">{s.base_url}</p>
                        )}
                      </div>
                      <div className="flex gap-1.5 flex-wrap justify-end">
                        {s.is_enabled && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-ai text-white">已啟用</span>
                        )}
                        {!supported && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-washi-card text-sumi-light border border-hairline">
                            尚未支援啟用
                          </span>
                        )}
                      </div>
                    </div>

                    <p className="text-xs text-sumi-light">
                      {s.is_configured ? `已設定 API key（${s.api_key_suffix ?? '****'}）` : '尚未設定 API key'}
                      {' · '}Timeout {s.timeout_seconds}s{' · '}最大輸出 {s.max_output_tokens} tokens{' · '}top_k {s.top_k}
                    </p>

                    {testResults[s.id] && (
                      <p className="text-xs text-sumi-light" role="status">{testResults[s.id]}</p>
                    )}

                    <div className="flex flex-wrap gap-3 pt-1">
                      <button
                        onClick={() => handleToggleEnabled(s)}
                        disabled={busyId === s.id || (!supported && !s.is_enabled) || !s.is_configured}
                        className="text-xs text-ai hover:text-sumi transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {s.is_enabled ? '停用' : '啟用'}
                      </button>
                      <button
                        onClick={() => handleTest(s)}
                        disabled={busyId === s.id || !supported || !s.is_configured}
                        className="text-xs text-ai hover:text-sumi transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        測試連線
                      </button>
                      <button
                        onClick={() => startEdit(s)}
                        className="text-xs text-sumi-light hover:text-sumi transition-colors"
                      >
                        編輯
                      </button>
                      <button
                        onClick={() => handleDelete(s)}
                        disabled={busyId === s.id}
                        className="text-xs text-vermillion hover:text-vermillion/70 transition-colors disabled:opacity-40"
                      >
                        刪除
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </AdminShell>
  )
}
