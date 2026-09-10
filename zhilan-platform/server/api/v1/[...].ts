/**
 * Nuxt Server Routes — 代理所有 API 请求到 FastAPI 后端
 * 开发环境: http://localhost:8000/api/v1
 * 生产环境: BACKEND_URL 环境变量
 */

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/api/v1'

export default defineEventHandler(async (event) => {
  const method = event.method
  const apiPath = event.path.replace(/^\/api\/v1/, '')

  const headers: Record<string, string> = {}
  const contentType = getHeader(event, 'content-type')
  if (contentType) headers['content-type'] = contentType

  try {
    const response = await $fetch(`${BACKEND_URL}${apiPath}`, {
      method: method as any,
      headers,
      body: method !== 'GET' && method !== 'HEAD' ? await readBody(event).catch(() => undefined) : undefined,
      query: getQuery(event),
    })

    setResponseStatus(event, 200)
    return response
  } catch (err: any) {
    setResponseStatus(event, err.statusCode || 500)
    return {
      detail: err.message || 'Backend connection failed',
      status: err.statusCode || 500,
    }
  }
})
