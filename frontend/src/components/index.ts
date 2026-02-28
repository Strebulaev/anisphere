// Компоненты поиска
export { default as SearchBar } from './Search/SearchBar.vue'
export { default as SearchSuggestions } from './Search/SearchSuggestions.vue'

// Компоненты фильтров
export { default as FilterBlock } from './Filters/FilterBlock.vue'
export { default as GenreFilter } from './Filters/GenreFilter.vue'
export { default as YearFilter } from './Filters/YearFilter.vue'
export { default as StatusFilter } from './Filters/StatusFilter.vue'
export { default as TypeFilter } from './Filters/TypeFilter.vue'
export { default as EpisodesFilter } from './Filters/EpisodesFilter.vue'
export { default as RatingFilter } from './Filters/RatingFilter.vue'
export { default as ActiveFilters } from './Filters/ActiveFilters.vue'
export { default as SortDropdown } from './Filters/SortDropdown.vue'
export { default as ItemsPerPage } from './Filters/ItemsPerPage.vue'

// Компоненты карточек
export { default as AnimeCard } from './Cards/AnimeCard.vue'
export { default as PlaylistCard } from './Cards/PlaylistCard.vue'
export { default as UserCard } from './Cards/UserCard.vue'

// Компоненты модальных окон
export { 
  ReminderModal,
  QuickViewModal,
  PlaylistSelectModal,
  PlaylistCreateModal,
  ReportModal
} from './Modals'

// Модуль навигационных элементов
export {
  Breadcrumbs,
  Pagination,
  LoadMoreButton
} from './Navigation'

// Модуль информационных блоков
export {
  PageTitle,
  LoadingState,
  ErrorState,
  EmptyState,
  RecommendationBanner
} from './Info'

// Модуль кнопок действий
export {
  CollectionButton,
  ShareButton,
  ReportButton,
  BackButton,
  AddToFavoriteButton
} from './Buttons'

// Модуль уведомлений
export {
  Toast,
  ToastContainer,
  useToast
} from './Notifications'

// Модуль секций аниме
export {
  AnimeSection,
  RandomSection
} from './AnimeSections'
