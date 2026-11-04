import { apiClient } from './client'
import { ChatMessage, ChatResponse } from './types'

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  context: string = ''
): Promise<ChatResponse> {
  const res = await apiClient.post<ChatResponse>('/surveillance/chat', {
    message,
    history,
    context,
  }, {
    timeout: 90000,
  })
  return res.data
}
