import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Person {
  id: number
  name: string
  name_jp: string
  slug: string
  description: string
  photo_url: string | null
  birth_date: string | null
  roles: string[]
  roles_display: string[]
  works_count: number
  anime_count: number
  created_at: string
}

export interface PersonDetail extends Person {
  related_anime: any[]
}

export interface PeopleParams {
  page?: number
  page_size?: number
  search?: string
  role?: string
  ordering?: string
}

const peopleApi = {
  // Получить список персон
  getPeople: (params?: PeopleParams): Promise<AxiosResponse<{
    results: Person[]
    count: number
    next: string | null
    previous: string | null
  }>> => {
    return apiClient.get('/dubs/people/', { params })
  },

  // Получить конкретную персону
  getPerson: (id: number): Promise<AxiosResponse<PersonDetail>> => {
    return apiClient.get<PersonDetail>(`/dubs/people/${id}/`)
  },

  // Получить аниме с участием персоны
  getPersonAnime: (id: number): Promise<AxiosResponse<any>> => {
    return apiClient.get(`/dubs/people/${id}/anime/`)
  },

  // Поиск персон
  searchPeople: (query: string, limit: number = 10): Promise<AxiosResponse<{
    results: Person[]
    count: number
  }>> => {
    return apiClient.get('/dubs/people/', {
      params: { search: query, page_size: limit }
    })
  }
}

export default peopleApi
