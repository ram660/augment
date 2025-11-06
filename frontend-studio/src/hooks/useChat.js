import { useState } from 'react'
import axios from 'axios'

export function useChat(homeId) {
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (message, selectedNodes, conversationHistory) => {
    setIsLoading(true)

    try {
      console.log('Sending chat message:', {
        message,
        homeId,
        selectedNodes,
        historyLength: conversationHistory.length
      })

      // Build conversation history in the format expected by backend
      const history = conversationHistory.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }))

      // Build context information about selected nodes
      const selectedRooms = selectedNodes.filter(n => n.type === 'room')
      const selectedImages = selectedNodes.filter(n => n.type === 'image')

      let contextMessage = message

      // Enhance message with selection context
      if (selectedRooms.length > 0 || selectedImages.length > 0) {
        const contextParts = []

        if (selectedRooms.length > 0) {
          const roomNames = selectedRooms.map(n => n.data.name).join(', ')
          contextParts.push(`Selected rooms: ${roomNames}`)
        }

        if (selectedImages.length > 0) {
          contextParts.push(`Selected images: ${selectedImages.length} image(s)`)
        }

        contextMessage = `${message}\n\n[Context: ${contextParts.join('; ')}]`
      }

      const response = await axios.post('/api/digital-twin/chat', {
        message: contextMessage,
        home_id: homeId,
        conversation_history: history
      })

      console.log('Chat response:', response.data)

      return response.data.response
    } catch (error) {
      console.error('Error sending message:', error)
      console.error('Error details:', error.response?.data)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return { sendMessage, isLoading }
}

