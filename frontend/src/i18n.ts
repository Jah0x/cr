import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const storageKey = 'language'
const supportedLanguages = ['ru', 'en'] as const

type SupportedLanguage = (typeof supportedLanguages)[number]

const detectInitialLanguage = (): SupportedLanguage => {
  const stored = localStorage.getItem(storageKey)
  if (stored && supportedLanguages.includes(stored as SupportedLanguage)) {
    return stored as SupportedLanguage
  }

  const browserLanguages = navigator.languages ?? [navigator.language]
  const normalized = browserLanguages.map((lang) => lang.toLowerCase())
  if (normalized.some((lang) => lang.startsWith('ru'))) {
    return 'ru'
  }
  if (normalized.some((lang) => lang.startsWith('en'))) {
    return 'en'
  }
  return 'ru'
}

const resources = {
  en: {
    translation: {
      language: {
        label: 'Language',
        ru: 'Russian',
        en: 'English'
      },
      nav: {
        platform: 'Platform',
        tenants: 'Tenants',
        tenantConsole: 'Tenant Console',
        admin: 'Admin',
        pos: 'POS',
        finance: 'Finance',
        settings: 'Settings'
      },
      common: {
        add: 'Add',
        save: 'Save',
        saving: 'Saving...',
        cancel: 'Cancel',
        create: 'Create',
        loading: 'Loading...',
        retry: 'Retry',
        yes: 'Yes',
        no: 'No',
        status: 'Status',
        schema: 'Schema',
        revision: 'Revision',
        head: 'Head',
        primary: 'Primary',
        remove: 'Remove',
        copy: 'Copy',
        copied: 'Copied',
        email: 'Email',
        password: 'Password'
      },
      errors: {
        loginFailed: 'Login failed',
        requestTimeout: 'Request timed out. Please try again.',
        requestCancelled: 'Request was cancelled. Please try again.',
        invalidPlatformCredentials: 'Invalid platform credentials.',
        inviteInvalid: 'Invite is invalid or expired.',
        inviteTokenRequired: 'Invite token is required.',
        passwordLength: 'Password must be at least 8 characters.',
        passwordMismatch: 'Passwords do not match.',
        registrationFailed: 'Unable to complete registration.',
        loadTenantsFailed: 'Unable to load tenants.',
        loadTenantSettingsFailed: 'Unable to load tenant settings.',
        loadTenantSettingsMessage: 'Failed to load tenant settings.',
        finalizeSaleFailed: 'Unable to finalize sale.',
        createTenantFailed: 'Unable to create tenant.',
        addItemsBeforeFinalize: 'Add items to the cart before finalizing.'
      },
      login: {
        title: 'Login',
        signIn: 'Sign in',
        emailPlaceholder: 'Email',
        passwordPlaceholder: 'Password'
      },
      register: {
        title: 'Complete registration',
        invitedEmail: 'Invited email',
        inviteTokenPlaceholder: 'Invite token',
        passwordPlaceholder: 'Password',
        confirmPasswordPlaceholder: 'Confirm password',
        setPassword: 'Set password'
      },
      platformLogin: {
        title: 'Platform Access',
        subtitle: 'Sign in with the platform owner credentials.',
        signIn: 'Sign in'
      },
      admin: {
        title: 'Admin',
        catalog: 'Catalog',
        categoryPlaceholder: 'Category',
        addCategory: 'Add Category',
        brandPlaceholder: 'Brand',
        addBrand: 'Add Brand',
        linePlaceholder: 'Line',
        addLine: 'Add Line',
        brandSelect: 'Brand',
        skuPlaceholder: 'SKU',
        productPlaceholder: 'Product',
        pricePlaceholder: 'Price',
        addProduct: 'Add Product',
        suppliersPurchasing: 'Suppliers & Purchasing',
        supplierPlaceholder: 'Supplier',
        addSupplier: 'Add Supplier',
        newInvoice: 'New Invoice',
        workingInvoice: 'Working invoice {{id}}',
        productSelect: 'Product',
        qtyPlaceholder: 'Qty',
        costPlaceholder: 'Cost',
        addItem: 'Add Item',
        postInvoice: 'Post Invoice',
        stock: 'Stock',
        adjust: 'Adjust',
        stockLevels: 'Stock Levels',
        reports: 'Reports',
        loadSummary: 'Load Summary',
        totalSales: 'Total sales',
        totalPurchases: 'Total purchases',
        grossMargin: 'Gross margin'
      },
      pos: {
        title: 'POS',
        searchProducts: 'Search products',
        cart: 'Cart',
        emptyCart: 'No items in cart',
        subtotal: 'Subtotal',
        payments: 'Payments',
        amount: 'Amount',
        reference: 'Reference',
        addPayment: 'Add',
        due: 'Due',
        finalize: 'Finalize Sale',
        sale: 'Sale',
        status: 'Status',
        total: 'Total',
        remove: 'Remove',
        paymentMethodCash: 'Cash',
        paymentMethodCard: 'Card',
        paymentMethodExternal: 'External'
      },
      finance: {
        title: 'Finance',
        expenseCategories: 'Expense Categories',
        categoryName: 'Category name',
        addCategory: 'Add Category',
        logExpense: 'Log Expense',
        amount: 'Amount',
        category: 'Category',
        paymentMethod: 'Payment method',
        note: 'Note',
        saveExpense: 'Save Expense',
        pnlSummary: 'P&L Summary',
        today: 'Today',
        week: 'Week',
        month: 'Month',
        totalSales: 'Total sales',
        cogs: 'COGS',
        grossProfit: 'Gross profit',
        expenses: 'Expenses',
        netProfit: 'Net profit',
        expensesTitle: 'Expenses',
        noNote: 'No note'
      },
      settings: {
        loading: 'Loading settings...',
        noSettings: 'No settings available.',
        title: 'Tenant settings',
        subtitle: 'Manage enabled modules, feature flags, and UI preferences.',
        modules: 'Modules',
        features: 'Features',
        uiPreferences: 'UI preferences',
        inactive: 'inactive',
        compactNav: 'Compact navigation',
        showHelp: 'Show help tips',
        errorTitle: 'Unable to load tenant settings.'
      },
      platformTenants: {
        title: 'Tenants',
        createTenant: 'Create tenant',
        loading: 'Loading tenants...',
        codeLabel: 'Code',
        migrateTenant: 'Migrate tenant',
        migrating: 'Migrating...',
        tenantName: 'Tenant name',
        tenantCode: 'Tenant code',
        tenantCodeReadOnly: 'Tenant code cannot be edited.',
        statusActive: 'active',
        statusInactive: 'inactive',
        schemaExists: 'Schema exists',
        lastError: 'Last error',
        domains: 'Domains',
        addDomain: 'Add domain',
        inviteLink: 'Invite link',
        generateInvite: 'Generate invite',
        expires: 'Expires',
        users: 'Users',
        deactivate: 'Deactivate',
        activate: 'Activate',
        deleteUserConfirm: 'Delete this user?',
        delete: 'Delete',
        userEmail: 'user email',
        rolesPlaceholder: 'roles (comma separated)',
        passwordMode: 'Password',
        inviteMode: 'Invite',
        passwordPlaceholder: 'password',
        createInvite: 'Create invite',
        addUser: 'Add user',
        domainPlaceholder: 'domain.example.com',
        inviteEmailPlaceholder: 'email@example.com',
        rolePlaceholder: 'role'
      },
      platformTenantCreate: {
        title: 'Create tenant',
        tenantName: 'Tenant name',
        tenantCode: 'Tenant code',
        ownerEmail: 'Owner email',
        templateId: 'Template id (optional)',
        tenantUrl: 'Tenant URL',
        inviteUrl: 'Invite URL'
      }
    }
  },
  ru: {
    translation: {
      language: {
        label: 'Язык',
        ru: 'Русский',
        en: 'Английский'
      },
      nav: {
        platform: 'Платформа',
        tenants: 'Тенанты',
        tenantConsole: 'Консоль арендатора',
        admin: 'Админ',
        pos: 'Касса',
        finance: 'Финансы',
        settings: 'Настройки'
      },
      common: {
        add: 'Добавить',
        save: 'Сохранить',
        saving: 'Сохранение...',
        cancel: 'Отмена',
        create: 'Создать',
        loading: 'Загрузка...',
        retry: 'Повторить',
        yes: 'Да',
        no: 'Нет',
        status: 'Статус',
        schema: 'Схема',
        revision: 'Ревизия',
        head: 'Head',
        primary: 'Основной',
        remove: 'Удалить',
        copy: 'Копировать',
        copied: 'Скопировано',
        email: 'Email',
        password: 'Пароль'
      },
      errors: {
        loginFailed: 'Не удалось войти',
        requestTimeout: 'Время запроса истекло. Попробуйте снова.',
        requestCancelled: 'Запрос был отменен. Попробуйте снова.',
        invalidPlatformCredentials: 'Неверные платформенные учетные данные.',
        inviteInvalid: 'Приглашение недействительно или просрочено.',
        inviteTokenRequired: 'Требуется токен приглашения.',
        passwordLength: 'Пароль должен быть не короче 8 символов.',
        passwordMismatch: 'Пароли не совпадают.',
        registrationFailed: 'Не удалось завершить регистрацию.',
        loadTenantsFailed: 'Не удалось загрузить список тенантов.',
        loadTenantSettingsFailed: 'Не удалось загрузить настройки тенанта.',
        loadTenantSettingsMessage: 'Не удалось загрузить настройки тенанта.',
        finalizeSaleFailed: 'Не удалось завершить продажу.',
        createTenantFailed: 'Не удалось создать тенанта.',
        addItemsBeforeFinalize: 'Добавьте товары в корзину перед завершением.'
      },
      login: {
        title: 'Вход',
        signIn: 'Войти',
        emailPlaceholder: 'Email',
        passwordPlaceholder: 'Пароль'
      },
      register: {
        title: 'Завершение регистрации',
        invitedEmail: 'Приглашенный email',
        inviteTokenPlaceholder: 'Токен приглашения',
        passwordPlaceholder: 'Пароль',
        confirmPasswordPlaceholder: 'Подтвердите пароль',
        setPassword: 'Установить пароль'
      },
      platformLogin: {
        title: 'Доступ к платформе',
        subtitle: 'Войдите с учетными данными владельца платформы.',
        signIn: 'Войти'
      },
      admin: {
        title: 'Админ',
        catalog: 'Каталог',
        categoryPlaceholder: 'Категория',
        addCategory: 'Добавить категорию',
        brandPlaceholder: 'Бренд',
        addBrand: 'Добавить бренд',
        linePlaceholder: 'Линейка',
        addLine: 'Добавить линейку',
        brandSelect: 'Бренд',
        skuPlaceholder: 'SKU',
        productPlaceholder: 'Товар',
        pricePlaceholder: 'Цена',
        addProduct: 'Добавить товар',
        suppliersPurchasing: 'Поставщики и закупки',
        supplierPlaceholder: 'Поставщик',
        addSupplier: 'Добавить поставщика',
        newInvoice: 'Новая накладная',
        workingInvoice: 'Текущая накладная {{id}}',
        productSelect: 'Товар',
        qtyPlaceholder: 'Кол-во',
        costPlaceholder: 'Себестоимость',
        addItem: 'Добавить позицию',
        postInvoice: 'Провести накладную',
        stock: 'Склад',
        adjust: 'Корректировать',
        stockLevels: 'Остатки',
        reports: 'Отчеты',
        loadSummary: 'Загрузить сводку',
        totalSales: 'Продажи',
        totalPurchases: 'Закупки',
        grossMargin: 'Валовая маржа'
      },
      pos: {
        title: 'Касса',
        searchProducts: 'Поиск товаров',
        cart: 'Корзина',
        emptyCart: 'Корзина пуста',
        subtotal: 'Подытог',
        payments: 'Оплаты',
        amount: 'Сумма',
        reference: 'Комментарий',
        addPayment: 'Добавить',
        due: 'К оплате',
        finalize: 'Завершить продажу',
        sale: 'Продажа',
        status: 'Статус',
        total: 'Итого',
        remove: 'Удалить',
        paymentMethodCash: 'Наличные',
        paymentMethodCard: 'Карта',
        paymentMethodExternal: 'Внешний'
      },
      finance: {
        title: 'Финансы',
        expenseCategories: 'Категории расходов',
        categoryName: 'Название категории',
        addCategory: 'Добавить категорию',
        logExpense: 'Записать расход',
        amount: 'Сумма',
        category: 'Категория',
        paymentMethod: 'Способ оплаты',
        note: 'Комментарий',
        saveExpense: 'Сохранить расход',
        pnlSummary: 'Отчет о прибылях и убытках',
        today: 'Сегодня',
        week: 'Неделя',
        month: 'Месяц',
        totalSales: 'Продажи',
        cogs: 'Себестоимость',
        grossProfit: 'Валовая прибыль',
        expenses: 'Расходы',
        netProfit: 'Чистая прибыль',
        expensesTitle: 'Расходы',
        noNote: 'Без комментария'
      },
      settings: {
        loading: 'Загрузка настроек...',
        noSettings: 'Настройки недоступны.',
        title: 'Настройки тенанта',
        subtitle: 'Управляйте модулями, фичами и настройками интерфейса.',
        modules: 'Модули',
        features: 'Функции',
        uiPreferences: 'Предпочтения интерфейса',
        inactive: 'неактивен',
        compactNav: 'Компактная навигация',
        showHelp: 'Показывать подсказки',
        errorTitle: 'Не удалось загрузить настройки тенанта.'
      },
      platformTenants: {
        title: 'Тенанты',
        createTenant: 'Создать тенанта',
        loading: 'Загрузка тенантов...',
        codeLabel: 'Код',
        migrateTenant: 'Мигрировать тенанта',
        migrating: 'Миграция...',
        tenantName: 'Название тенанта',
        tenantCode: 'Код тенанта',
        tenantCodeReadOnly: 'Код тенанта нельзя редактировать.',
        statusActive: 'активен',
        statusInactive: 'неактивен',
        schemaExists: 'Схема существует',
        lastError: 'Последняя ошибка',
        domains: 'Домены',
        addDomain: 'Добавить домен',
        inviteLink: 'Ссылка приглашения',
        generateInvite: 'Создать приглашение',
        expires: 'Истекает',
        users: 'Пользователи',
        deactivate: 'Деактивировать',
        activate: 'Активировать',
        deleteUserConfirm: 'Удалить этого пользователя?',
        delete: 'Удалить',
        userEmail: 'email пользователя',
        rolesPlaceholder: 'роли (через запятую)',
        passwordMode: 'Пароль',
        inviteMode: 'Приглашение',
        passwordPlaceholder: 'пароль',
        createInvite: 'Создать приглашение',
        addUser: 'Добавить пользователя',
        domainPlaceholder: 'domain.example.com',
        inviteEmailPlaceholder: 'email@example.com',
        rolePlaceholder: 'роль'
      },
      platformTenantCreate: {
        title: 'Создание тенанта',
        tenantName: 'Название тенанта',
        tenantCode: 'Код тенанта',
        ownerEmail: 'Email владельца',
        templateId: 'ID шаблона (опционально)',
        tenantUrl: 'URL тенанта',
        inviteUrl: 'URL приглашения'
      }
    }
  }
}

i18n.use(initReactI18next).init({
  resources,
  lng: detectInitialLanguage(),
  fallbackLng: 'ru',
  interpolation: {
    escapeValue: false
  }
})

i18n.on('languageChanged', (language) => {
  localStorage.setItem(storageKey, language)
})

export default i18n
