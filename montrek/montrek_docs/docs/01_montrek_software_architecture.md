Montrek Software Architecture

## Overview

Montrek is a Django framework that provides a structured approach to building data-driven applications. At its core, Montrek is designed around a clear and opinionated software architecture that emphasizes inheritance with dependency injection.

## Key Components

### MontrekRepository

The `MontrekRepository` class serves as the data access layer, encapsulating the logic for interacting with the underlying data storage. It provides a standardized interface for creating, reading, updating, and deleting data.

### MontrekManager

The `MontrekManager` class is the central component of the Montrek framework. It acts as an intermediary between the data access layer and the business logic layer, providing a unified interface for managing data and executing business logic.

### MontrekView

The `MontrekView` class is responsible for handling HTTP requests and rendering responses. It provides a flexible and extensible way to define views that can be used to display data, handle forms, and execute business logic.

### Differentiation between MontrekViews

Montrek provides several specialized view classes that cater to specific use cases:

*   `MontrekTemplateView`: A basic view class that renders a template with the provided context.
*   `MontrekListView`: A view class that displays a list of objects, providing features like pagination and filtering.
*   `MontrekDetailView`: A view class that displays a single object, providing features like editing and deletion.
*   `MontrekCreateView`: A view class that handles the creation of new objects.
*   `MontrekUpdateView`: A view class that handles the updating of existing objects.

### Connection to HTML Template

Montrek views use Django's built-in template engine to render HTML templates. The `MontrekView` class provides a `get_template_names` method that returns a list of template names to be used for rendering.

## Class Names and Source Module Paths

The following table lists the key classes and their corresponding source module paths:

| Class Name | Source Module Path |
| --- | --- |
| `MontrekRepository` | `baseclasses.repositories.montrek_repository` |
| `MontrekManager` | `baseclasses.managers.montrek_manager` |
| `MontrekView` | `baseclasses.views` |
| `MontrekTemplateView` | `baseclasses.views` |
| `MontrekListView` | `baseclasses.views` |
| `MontrekDetailView` | `baseclasses.views` |
| `MontrekCreateView` | `baseclasses.views` |
| `MontrekUpdateView` | `baseclasses.views` |

## Core App Layers

The core apps form layers. A module imports only modules of its own layer and of the layers below it, in code and in tests, so an install can take over the core layer by layer and run each layer's tests without the layers above.

| Layer | Apps |
| --- | --- |
| 0 | `montrek` (modules without app imports), `storage`, `tasks` |
| 1 | `baseclasses`, `user`, `middleware`, `rest_api`, `testing` |
| 2 | `reporting`, `mailing`, `info` |
| 3 | `process_pipeline`, `file_upload` |
| 4 | `montrek.settings`, `montrek.urls`, `montrek.media`, `montrek.wsgi`, `montrek.asgi` |

Apps that are not listed, such as `montrek_example`, are extensions above the core and may import any of it. `montrek/tests/test_layers.py` holds the table and fails when a core module imports a higher layer.

```
 Layer 4   montrek.settings · montrek.urls · montrek.media
                │  baseclasses, middleware, user
                ▼
 Layer 3   file_upload ─────────────► process_pipeline
                │ info, reporting,          │ mailing, reporting,
                │ storage, user             │ tasks, user
                ▼                           ▼
 Layer 2   info ◄────────► reporting ◄────────► mailing
                                │
                                └──► storage, tasks
                ▼                           ▼
 Layer 1   middleware ──► baseclasses ──► rest_api ──► user
                               ▲                         │
                               └─────────────────────────┘
           testing ──► baseclasses, middleware, user, storage
                ▼
 Layer 0   montrek (utils, celery_app, configuration, test runner, …)
           storage (no deps)        tasks ──► montrek.celery_app

 Every app in layers 1–4 also imports baseclasses and montrek (layer 0);
 the arrows for those are left out.
```

The base views in `baseclasses` offer features that the apps above them implement. Those apps plug them in rather than being imported:

- The views send the `baseclasses.signals.document_downloaded` signal for every document they hand out; `info` stores it in its download registry.
- `reporting` registers the PDF export and the history table, and `file_upload` the simple file upload, with `baseclasses.view_plugins.ViewPlugins` in their `AppConfig.ready()`. A view that uses one of these features without its app raises `ImproperlyConfigured`.

## Summary

Montrek's software architecture is designed to provide a clear and structured approach to building data-driven applications. By emphasizing inheritance with dependency injection, Montrek enables developers to create robust and maintainable applications with ease. The framework's key components, including `MontrekRepository`, `MontrekManager`, and `MontrekView`, work together to provide a unified interface for managing data and executing business logic. With its flexible and extensible design, Montrek is an ideal choice for building complex data-driven applications.
