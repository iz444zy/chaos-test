import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Session } from '@supabase/supabase-js'
import './App.css'
import { supabase, supabaseConfigured } from './supabase'

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type RecipeSummary = { id: number; name: string; status: 'DEVELOPING' | 'FINALIZED'; attempts_count: number; most_recent_attempt: string | null; thumbnail_url: string | null }
type Attempt = { id: number; name: string; attempted_on: string; ingredients: string[]; instructions: string[]; notes?: string; rating?: number | null; techniques?: string; timing_notes?: string; media: { id: number; url: string; media_type: string; caption?: string }[] }
type Recipe = RecipeSummary & { description?: string; source_url?: string; ingredients: string[]; instructions: string[]; prep_time?: string; cook_time?: string; total_time?: string; yield_text?: string; finalized_instance_id?: number; parent_recipe_id?: number; instances: Attempt[] }
type RecipeDraft = { name: string; description: string; source_url: string; ingredients: string; instructions: string; prep_time: string; cook_time: string; total_time: string; yield_text: string }

const blankDraft: RecipeDraft = { name: '', description: '', source_url: '', ingredients: '', instructions: '', prep_time: '', cook_time: '', total_time: '', yield_text: '' }
const lines = (value: string) => value.split('\n').map((item) => item.trim()).filter(Boolean)
const draftFromRecipe = (recipe: Partial<Recipe>): RecipeDraft => ({
  name: recipe.name ?? '', description: recipe.description ?? '', source_url: recipe.source_url ?? '',
  ingredients: (recipe.ingredients ?? []).join('\n'), instructions: (recipe.instructions ?? []).join('\n'),
  prep_time: recipe.prep_time ?? '', cook_time: recipe.cook_time ?? '', total_time: recipe.total_time ?? '', yield_text: recipe.yield_text ?? '',
})

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [devAccessToken, setDevAccessToken] = useState<string | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [page, setPage] = useState<'welcome' | 'dashboard' | 'editor' | 'import' | 'profile'>('welcome')
  const [recipes, setRecipes] = useState<RecipeSummary[]>([])
  const [selected, setSelected] = useState<Recipe | null>(null)
  const [draft, setDraft] = useState<RecipeDraft>(blankDraft)
  const [email, setEmail] = useState('')
  const [magicLinkSent, setMagicLinkSent] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [message, setMessage] = useState('')
  const accessToken = devAccessToken ?? session?.access_token ?? null
  const signedIn = Boolean(accessToken)
  const devLoginEnabled = import.meta.env.VITE_ENABLE_DEV_LOGIN_BYPASS === 'true'

  const request = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    const response = await fetch(`${apiUrl}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}), ...options.headers },
    })
    if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: 'Request failed' }))).detail)
    return response.json()
  }
  const loadRecipes = async () => { if (accessToken) setRecipes(await request<RecipeSummary[]>('/recipes')) }
  const openRecipe = async (id: number) => { setSelected(await request<Recipe>(`/recipes/${id}`)); setPage('profile') }

  useEffect(() => {
    if (!supabase) {
      setAuthReady(true)
      return
    }
    const client = supabase
    let active = true
    const restoreSession = async () => {
      try {
        const code = new URLSearchParams(window.location.search).get('code')
        if (code) {
          const { error } = await client.auth.exchangeCodeForSession(code)
          if (error) throw error
          window.history.replaceState({}, document.title, window.location.pathname)
        }
        const { data, error } = await client.auth.getSession()
        if (error) throw error
        if (active) setSession(data.session)
      } catch (error) {
        if (active) setAuthError((error as Error).message)
      } finally {
        if (active) setAuthReady(true)
      }
    }
    void restoreSession()
    const { data: { subscription } } = client.auth.onAuthStateChange((_event, nextSession) => {
      if (active) setSession(nextSession)
    })
    return () => {
      active = false
      subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    if (!authReady) return
    setPage(signedIn ? 'dashboard' : 'welcome')
  }, [authReady, signedIn])

  useEffect(() => { void loadRecipes().catch((error: Error) => setMessage(error.message)) }, [accessToken])

  const authenticate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!supabase) {
      setAuthError('Supabase is not configured. Add the Vite environment variables and restart the frontend.')
      return
    }
    setAuthBusy(true)
    setAuthError('')
    setMagicLinkSent(false)
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: window.location.origin },
      })
      if (error) throw error
      setMagicLinkSent(true)
    } catch (error) {
      setAuthError((error as Error).message)
    } finally {
      setAuthBusy(false)
    }
  }
  const devLogin = async () => {
    setAuthBusy(true)
    setAuthError('')
    try {
      const response = await fetch(`${apiUrl}/auth/dev-login`, { method: 'POST' })
      if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: 'Development login failed' }))).detail)
      const payload = await response.json() as { access_token: string }
      setDevAccessToken(payload.access_token)
    } catch (error) {
      setAuthError((error as Error).message)
    } finally {
      setAuthBusy(false)
    }
  }
  const logout = async () => {
    setDevAccessToken(null)
    if (supabase) {
      const { error } = await supabase.auth.signOut()
      if (error) setMessage(error.message)
    }
    setSession(null)
    setRecipes([])
  }
  const saveRecipe = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const payload = { ...draft, ingredients: lines(draft.ingredients), instructions: lines(draft.instructions) }
      const recipe = await request<Recipe>(selected ? `/recipes/${selected.id}` : '/recipes', { method: selected ? 'PUT' : 'POST', body: JSON.stringify(payload) })
      await loadRecipes(); setSelected(recipe); setPage('profile'); setMessage('Recipe saved.')
    } catch (error) { setMessage((error as Error).message) }
  }
  const importRecipe = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const url = new FormData(event.currentTarget).get('url')
    try { setDraft(draftFromRecipe(await request<Recipe & { parse_succeeded: boolean }>('/imports/preview', { method: 'POST', body: JSON.stringify({ url }) }))); setSelected(null); setPage('editor'); setMessage('Review the imported details before saving.') } catch (error) { setMessage((error as Error).message) }
  }
  const newAttempt = async () => {
    if (!selected) return
    try { await request(`/recipes/${selected.id}/instances/clone`, { method: 'POST' }); await openRecipe(selected.id); setMessage('A new editable attempt was created from the latest version.') } catch (error) { setMessage((error as Error).message) }
  }
  const finalize = async (attempt: Attempt) => { if (!selected) return; try { const recipe = await request<Recipe>(`/recipes/${selected.id}/finalize`, { method: 'POST', body: JSON.stringify({ instance_id: attempt.id }) }); setSelected(recipe); await loadRecipes(); setMessage('This version is now preserved as the finalized recipe.') } catch (error) { setMessage((error as Error).message) } }
  const variant = async () => { if (!selected) return; try { const recipe = await request<Recipe>(`/recipes/${selected.id}/variants`, { method: 'POST' }); await loadRecipes(); setSelected(recipe); setPage('editor'); setDraft(draftFromRecipe(recipe)); setMessage('Editable variant created from the finalized recipe.') } catch (error) { setMessage((error as Error).message) } }

  const nav = <header><button className="brand" onClick={() => setPage(signedIn ? 'dashboard' : 'welcome')}>BatchBook</button>{signedIn && <button className="quiet" onClick={() => { void logout() }}>Log out</button>}</header>
  if (!authReady) return <main>{nav}<section className="hero"><p>Restoring your session…</p></section></main>
  if (page === 'welcome') return <main>{nav}<section className="hero"><p className="eyebrow">RECIPE DEVELOPMENT TRACKER</p><h1>Make every version worth remembering.</h1><p>BatchBook is a home for the details, experiments, and small discoveries behind the recipes you make again.</p><form className="auth card" onSubmit={authenticate}><h2>Sign in to your kitchen notebook</h2><label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} name="email" type="email" placeholder="you@example.com" required /></label><button disabled={authBusy || !supabaseConfigured}>{authBusy ? 'Sending…' : 'Email me a sign-in link'}</button>{magicLinkSent && <p className="notice">Check your inbox for a sign-in link. It may take a minute to arrive.</p>}{authError && <p className="notice">{authError}</p>}</form>{devLoginEnabled && <button className="secondary" onClick={() => { void devLogin() }} disabled={authBusy}>Development login bypass</button>}</section><Notice message={message}/></main>

  if (page === 'dashboard') return <main>{nav}<section className="page-heading"><div><p className="eyebrow">YOUR KITCHEN NOTEBOOK</p><h1>My Recipes</h1></div><div><button onClick={() => { setSelected(null); setDraft(blankDraft); setPage('editor') }}>+ New Recipe</button><button className="secondary" onClick={() => setPage('import')}>Import Recipe</button></div></section><RecipeGroup title="Developing" recipes={recipes.filter((recipe) => recipe.status === 'DEVELOPING')} openRecipe={openRecipe}/><RecipeGroup title="Finalized" recipes={recipes.filter((recipe) => recipe.status === 'FINALIZED')} openRecipe={openRecipe}/><Notice message={message}/></main>
  if (page === 'import') return <main>{nav}<section className="narrow"><p className="eyebrow">START FROM A SOURCE</p><h1>Import a recipe</h1><p>We’ll look for structured recipe metadata. You can correct every detail before it becomes part of your notebook.</p><form className="card" onSubmit={importRecipe}><label>Recipe URL<input name="url" type="url" placeholder="https://example.com/recipe" required /></label><button>Extract Recipe Details</button></form></section><Notice message={message}/></main>
  if (page === 'editor') return <main>{nav}<section className="narrow"><p className="eyebrow">{selected ? 'EDIT RECIPE PROFILE' : 'NEW RECIPE PROFILE'}</p><h1>{selected ? selected.name : 'Create a recipe'}</h1><form className="editor card" onSubmit={saveRecipe}><label>Name<input required value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}/></label><label>Description<textarea value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })}/></label><label>Source URL<input type="url" value={draft.source_url} onChange={(e) => setDraft({ ...draft, source_url: e.target.value })}/></label><div className="grid"><label>Prep time<input value={draft.prep_time} onChange={(e) => setDraft({ ...draft, prep_time: e.target.value })}/></label><label>Cook time<input value={draft.cook_time} onChange={(e) => setDraft({ ...draft, cook_time: e.target.value })}/></label><label>Total time<input value={draft.total_time} onChange={(e) => setDraft({ ...draft, total_time: e.target.value })}/></label><label>Yield<input value={draft.yield_text} onChange={(e) => setDraft({ ...draft, yield_text: e.target.value })}/></label></div><label>Ingredients <span>One per line</span><textarea value={draft.ingredients} onChange={(e) => setDraft({ ...draft, ingredients: e.target.value })}/></label><label>Procedure <span>One step per line</span><textarea value={draft.instructions} onChange={(e) => setDraft({ ...draft, instructions: e.target.value })}/></label><button>Save Recipe Profile</button></form></section><Notice message={message}/></main>
  if (page === 'profile' && selected) return <main>{nav}<section className="page-heading"><div><p className="eyebrow">{selected.status === 'FINALIZED' ? 'FINALIZED RECIPE' : 'DEVELOPING RECIPE'}</p><h1>{selected.name}</h1><p>{selected.description || 'No description yet.'}</p></div>{selected.status === 'FINALIZED' ? <button onClick={variant}>Create New Variant</button> : <div><button onClick={newAttempt}>Create Next Attempt</button><button className="secondary" onClick={() => { setDraft(draftFromRecipe(selected)); setPage('editor') }}>Edit Profile</button></div>}</section><section className="details card"><div><b>Status</b><span>{selected.status === 'FINALIZED' ? 'Finalized' : 'Developing'}</span></div><div><b>Source</b><span>{selected.source_url || 'Created manually'}</span></div><div><b>Base recipe</b><span>{selected.ingredients.length} ingredients · {selected.instructions.length} steps</span></div></section><section><h2>Attempt history</h2>{selected.instances.length === 0 ? <div className="empty card"><p>No attempts recorded. Create your first attempt to capture what you actually make.</p><button onClick={newAttempt}>Create First Attempt</button></div> : <div className="attempts">{[...selected.instances].reverse().map((attempt) => <article className="attempt card" key={attempt.id}><div><p className="eyebrow">{new Date(`${attempt.attempted_on}T00:00:00`).toLocaleDateString()}</p><h2>{attempt.name}</h2><p>{attempt.ingredients.length} ingredients · {attempt.instructions.length} steps {attempt.rating ? `· ${attempt.rating}/5` : ''}</p>{attempt.notes && <p>{attempt.notes}</p>}</div>{selected.status !== 'FINALIZED' && <button className="secondary" onClick={() => finalize(attempt)}>Finalize This Recipe</button>}{selected.finalized_instance_id === attempt.id && <span className="pill">Preserved final version</span>}</article>)}</div>}</section><Notice message={message}/></main>
  return null
}

function RecipeGroup({ title, recipes, openRecipe }: { title: string; recipes: RecipeSummary[]; openRecipe: (id: number) => void }) {
  return <section className="group"><h2>{title} <span>{recipes.length}</span></h2>{recipes.length ? <div className="recipe-grid">{recipes.map((recipe) => <button className="recipe-card card" key={recipe.id} onClick={() => openRecipe(recipe.id)}>{recipe.thumbnail_url && <img src={recipe.thumbnail_url} alt="" />}<p className="eyebrow">{recipe.status === 'FINALIZED' ? 'FINALIZED' : 'IN DEVELOPMENT'}</p><h2>{recipe.name}</h2><p>{recipe.attempts_count} attempt{recipe.attempts_count === 1 ? '' : 's'} {recipe.most_recent_attempt && `· Last made ${new Date(`${recipe.most_recent_attempt}T00:00:00`).toLocaleDateString()}`}</p></button>)}</div> : <p className="muted">Nothing here yet.</p>}</section>
}
function Notice({ message }: { message: string }) { return message ? <p className="notice">{message}</p> : null }
export default App
