FROM php:8.2-cli

RUN apt-get update && apt-get install -y \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Copy composer files first for cache
COPY composer.json ./

# Install dependencies
RUN composer install --no-dev --optimize-autoloader

# Copy app code
COPY index.php ./

CMD ["php", "-S", "0.0.0.0:8000", "index.php"]
