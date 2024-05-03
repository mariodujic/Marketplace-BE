# Info

This is KMP MarketPlace backend app.

# Run

To run application in a Docker container:

1. Install Docker on your system.

2. Build the Docker image:

    ```bash
    docker build -t my-app .
    ```

3. Run the Docker container with hot reload enabled:

    ```bash
    docker run -d -p 5000:5000 -v $(pwd):/app my-app
    ```

4. Access the application at `http://localhost:5000`.

# PaaS

## Used services

[Supabase](https://supabase.com/dashboard/project/ulwhvgtkewyxpcubqfjq) PostgreSQL.

# Graph

```mermaid
graph TD;
    subgraph Mobile App
        Auth[User Authentication];
        Catalog[Product Catalog];
        Cart[Shopping Cart];
        Order[Order Management];
        User[User];
    end

    subgraph Flask Backend
        AuthAPI[Auth API];
        ProductAPI[Product API];
        CartAPI[Cart API];
        OrderAPI[Order API];
        UserAPI[User API];
    end

    subgraph PostgreSQL Database
        UserTable[User Table];
        OrderTable[Order Table];
        CartTable[Cart Table];
    end

    subgraph PaymentGateway
        StripeProducts[Products];
    end

    Auth --> AuthAPI
    Catalog --> ProductAPI
    Cart --> CartAPI
    Order --> OrderAPI
    User --> UserAPI

    AuthAPI --> UserTable
    ProductAPI --> StripeProducts
    CartAPI --> CartTable
    OrderAPI --> OrderTable
    UserAPI --> UserTable
```