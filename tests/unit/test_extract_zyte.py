import pytest
from unittest.mock import MagicMock, patch, ANY
from nightcrawler.extract.s04_zyte import ZyteExtractor
from nightcrawler.base import PipelineResult, ExtractZyteData, MetaData
from copy import deepcopy


@pytest.fixture
def zyte_extractor():
    # Create a mock context required by ZyteExtractor
    context = MagicMock()
    context.zyte_filename = "dummy_zyte_filename.json"
    context.output_dir = "/tmp"
    return ZyteExtractor(context)


@patch.object(ZyteExtractor, "structure_results")
@patch.object(ZyteExtractor, "retrieve_response")
@patch.object(ZyteExtractor, "initiate_client")
def test_apply_method(
    mock_initiate_client,
    mock_retrieve_response,
    mock_structure_results,
    zyte_extractor,
):
    # Parameters: Input to the apply method
    input_pipeline_result = PipelineResult(
        meta=MetaData(keyword="test_keyword", numberOfResultsManuallySet=1),
        relevant_results=[{"url": "http://example.com/product1"}],
    )

    # Expected results from the internal methods
    expected_client = MagicMock()  # Mocked ZyteAPI client
    expected_config = {}  # Mocked configuration dictionary
    expected_retrieve_response = [{"product": {"name": "Product Name"}}]

    # Mock relevant_results to return a list of ExtractZyteData
    expected_relevant_results = [
        ExtractZyteData(
            url="http://example.com/product1",
            price="100USD",
            title="Product 1",
            fullDescription="Description 1",
            zyteExecutionTime=2,
            offerRoot="GOOGLE",
        )
    ]

    # Mock expected_errors results (no errors)
    exptected_errors = []

    # Set up mocks to return the expected results
    mock_initiate_client.return_value = (expected_client, expected_config)
    mock_retrieve_response.return_value = expected_retrieve_response
    mock_structure_results.return_value = expected_relevant_results, exptected_errors

    # Expected final result from the apply method
    # Copy meta and update numberOfResultsManuallySetAfterStage
    expected_meta = deepcopy(input_pipeline_result.meta)
    expected_meta.resultDate = ANY
    expected_meta.uuid = ANY
    expected_meta.resultStatistics = ANY

    expected_result = PipelineResult(
        meta=expected_meta, relevant_results=expected_relevant_results
    )

    # Call the method under test
    actual_result = zyte_extractor.apply(input_pipeline_result)

    # Assertions to verify each method is called correctly
    mock_initiate_client.assert_called_once()
    mock_retrieve_response.assert_called_once_with(
        expected_client, input_pipeline_result, expected_config, callback=ANY
    )
    mock_structure_results.assert_called_once_with(
        expected_retrieve_response, input_pipeline_result
    )

    # Assert that the actual result matches the expected result
    assert actual_result == expected_result
