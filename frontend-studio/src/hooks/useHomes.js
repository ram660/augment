import { useState, useEffect } from 'react'
import axios from 'axios'

export function useHomes() {
  const [homes, setHomes] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchHomes = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await axios.get('/api/digital-twin/homes')
        console.log('Fetched homes:', response.data)
        setHomes(response.data)
      } catch (err) {
        console.error('Error fetching homes:', err)
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchHomes()
  }, [])

  return { homes, isLoading, error }
}

