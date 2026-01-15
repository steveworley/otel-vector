<?php

require __DIR__ . '/vendor/autoload.php';

use OpenTelemetry\API\Globals;
use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\SDK\Trace\TracerProvider;
use OpenTelemetry\Contrib\Otlp\SpanExporter;
use OpenTelemetry\SDK\Trace\SpanProcessor\SimpleSpanProcessor;
use OpenTelemetry\SDK\Resource\ResourceInfo;
use OpenTelemetry\SDK\Resource\ResourceInfoFactory;
use OpenTelemetry\SemConv\ResourceAttributes;
use OpenTelemetry\SDK\Common\Attribute\Attributes;

// Configure OTLP Exporter
$transport = (new \OpenTelemetry\Contrib\Otlp\OtlpHttpTransportFactory())->create('http://otel-collector:4318/v1/traces', 'application/json');
$exporter = new SpanExporter($transport);

$resource = ResourceInfoFactory::emptyResource()->merge(ResourceInfo::create(Attributes::create([
    ResourceAttributes::SERVICE_NAME => 'php-app',
    ResourceAttributes::SERVICE_VERSION => 'v1.2.0-beta', // Simulated deployment version
    'deployment.environment' => 'poc',
    'application' => 'php-demo-app',
    'org.service.id' => '0000-000000000000',
    'org.service.name' => 'sre',
    'org.routing.target' => 'test-target',
])));

$tracerProvider = new TracerProvider(
    new SimpleSpanProcessor($exporter),
    null,
    $resource
);

$tracer = $tracerProvider->getTracer('php-app-tracer');

// PARSE SCENARIO
$scenario = $_GET['scenario'] ?? 'normal'; // normal, latency, error, saturation

// Start Root Span
$rootSpan = $tracer->spanBuilder('incoming_http_request')->setSpanKind(SpanKind::KIND_SERVER)->startSpan();
$rootSpan->activate();

// Simulate Golden Signals
try {
    // 1. SATURATION (Memory/CPU Simulation)
    // We add these as attributes so the vector DB can index "high saturation" events.
    $cpu_usage = rand(10, 40);
    $memory_usage = rand(200, 500); // MB

    if ($scenario === 'saturation') {
        $cpu_usage = rand(85, 99);
        $memory_usage = rand(800, 1024);
        echo "Simulating HIGH SATURATION...\n";
    }

    $rootSpan->setAttribute('host.cpu.utilization', $cpu_usage);
    $rootSpan->setAttribute('process.memory.usage', $memory_usage);


    // 2. LATENCY
    $sleep_ms = rand(50, 150);
    if ($scenario === 'latency') {
        $sleep_ms = rand(1000, 3000); // 1-3 seconds
        echo "Simulating HIGH LATENCY ({$sleep_ms}ms)...\n";
    }
    usleep($sleep_ms * 1000);

    // Business Logic Span
    $childSpan = $tracer->spanBuilder('process_request')->setSpanKind(SpanKind::KIND_INTERNAL)->startSpan();

    // 3. ERROR RATE
    if ($scenario === 'error') {
        echo "Simulating ERROR...\n";

        try {
            // Deterministic error source
            throw new Exception("Critical Database Connection Failure");
        } catch (Exception $e) {
            $childSpan->recordException($e);
            $childSpan->setStatus(StatusCode::STATUS_ERROR, "Simulated critical failure");

            // Simulate a code-level exception
            // This is required to match our Semantic Conventions
            // this defines what an error looks like to our organisation
            // and how we can identify it.
            $childSpan->setAttribute('code.filepath', __FILE__);
            $childSpan->setAttribute('code.lineno', __LINE__);
            $childSpan->setAttribute('code.function', 'process_request');
        }
        usleep(100000); // 100ms
        http_response_code(500); // Set HTTP status code for error scenario
    } else {
        $childSpan->setAttribute('status', 'success');
        echo "Processed successfully.\n";
    }

    $childSpan->end();

} catch (\Throwable $t) {
    $rootSpan->recordException($t);
    $rootSpan->setStatus(StatusCode::STATUS_ERROR, $t->getMessage());
} finally {
    $rootSpan->end();
    $tracerProvider->shutdown();
}
