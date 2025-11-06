import { useState, useEffect } from 'react'
import axios from 'axios'

export function useStudioData(homeId) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!homeId) return

    const fetchData = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Fetch home data from API - using the correct endpoint
        const response = await axios.get(`/api/digital-twin/homes/${homeId}`)
        const homeData = response.data

        console.log('Fetched home data:', homeData)

        // Transform data for studio
        const studioData = {
          home: {
            id: homeData.home_id,
            name: homeData.basic_info?.name || 'Home',
            type: homeData.home_type,
            address: homeData.basic_info?.address || '',
            square_footage: homeData.basic_info?.square_footage || 0,
            num_bedrooms: homeData.basic_info?.num_bedrooms || 0,
            num_bathrooms: homeData.basic_info?.num_bathrooms || 0
          },
          floor_plan: homeData.floor_plans?.[0] ? {
            id: homeData.floor_plans[0].id,
            image_url: homeData.floor_plans[0].image_url,
            rooms: homeData.rooms?.map((room, index) => ({
              id: room.id,
              name: room.name,
              room_type: room.room_type,
              floor_level: room.floor_level,
              materials_count: room.materials_count || 0,
              fixtures_count: room.fixtures_count || 0,
              products_count: room.products_count || 0,
              images_count: room.images_count || 0,
              area: room.dimensions?.area || 0,
              bounds: {
                // Auto-arrange in a grid for now
                x: (index % 4) * 200,
                y: Math.floor(index / 4) * 150,
                width: 180,
                height: 120
              }
            })) || []
          } : null,
          images: homeData.rooms?.flatMap(room =>
            room.images?.map((img, imgIndex) => ({
              id: img.id,
              url: img.image_url,
              room_id: room.id,
              room_name: room.name,
              is_analyzed: img.is_analyzed,
              position: null // Will be set by user or auto-arranged
            })) || []
          ) || []
        }

        console.log('Transformed studio data:', studioData)
        setData(studioData)
      } catch (err) {
        console.error('Error fetching studio data:', err)
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [homeId])

  return { data, isLoading, error }
}

