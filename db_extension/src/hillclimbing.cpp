#include "duckdb_extension.h"
#include <iostream>
#include <string>
#include <cstdio>
#include <memory>
#include <array>
#include <sstream>

DUCKDB_EXTENSION_EXTERN

// Declarations of internal registration helper
void RegisterHillclimbingFunction(duckdb_connection connection);

// UDF scalar function implementation
static void HillclimbingOptimize(duckdb_function_info info, duckdb_data_chunk input, duckdb_vector output) {
    // Get chunk size
    idx_t input_size = duckdb_data_chunk_get_size(input);
    
    // Get query text vector
    duckdb_vector query_vec = duckdb_data_chunk_get_vector(input, 0);
    
    // Get pointers
    duckdb_string_t* query_data = (duckdb_string_t*)duckdb_vector_get_data(query_vec);
    
    for (idx_t row = 0; row < input_size; row++) {
        // Extract query string using DuckDB C API helpers
        uint32_t length = duckdb_string_t_length(query_data[row]);
        const char* data_ptr = duckdb_string_t_data(&query_data[row]);
        std::string query_str(data_ptr, length);
        
        // Write query_str to a temp file to avoid shell escaping issues
        std::string temp_sql_path = "/home/emil/projects/verified-hillclimbing-db/db_extension/temp_query.sql";
        FILE* sql_file = fopen(temp_sql_path.c_str(), "w");
        if (sql_file) {
            fwrite(query_str.c_str(), 1, query_str.length(), sql_file);
            fclose(sql_file);
        }
        
        // Command to execute run_optimizer
        std::string cmd = "uv run python -m db_extension.run_optimizer --file " + temp_sql_path + " 2>&1";
        
        // Execute popen and stream output
        char buffer[1024];
        FILE* pipe = popen(cmd.c_str(), "r");
        int exit_code = -1;
        if (pipe) {
            while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
                // Print live to standard out of the DuckDB CLI process
                std::cout << buffer << std::flush;
            }
            exit_code = pclose(pipe);
        }

        // Cleanup temp file
        remove(temp_sql_path.c_str());

        // Side effects (demo steps + result table) are on stdout; return empty on success.
        std::string output_str = (exit_code == 0) ? "" : "Hillclimbing optimization failed.";
        duckdb_vector_assign_string_element(output, row, output_str.c_str());
    }
}

// Function registration
void RegisterHillclimbingFunction(duckdb_connection connection) {
    // 1. Register main 'hillclimbing_optimize' function
    duckdb_scalar_function function = duckdb_create_scalar_function();
    duckdb_scalar_function_set_name(function, "hillclimbing_optimize");
    
    duckdb_logical_type param_type = duckdb_create_logical_type(DUCKDB_TYPE_VARCHAR);
    duckdb_scalar_function_add_parameter(function, param_type);
    
    duckdb_logical_type ret_type = duckdb_create_logical_type(DUCKDB_TYPE_VARCHAR);
    duckdb_scalar_function_set_return_type(function, ret_type);
    
    duckdb_destroy_logical_type(&param_type);
    duckdb_destroy_logical_type(&ret_type);
    
    duckdb_scalar_function_set_function(function, HillclimbingOptimize);
    
    duckdb_register_scalar_function(connection, function);
    duckdb_destroy_scalar_function(&function);
    
    // 2. Register alias 'hillclimbing'
    duckdb_scalar_function function_alias = duckdb_create_scalar_function();
    duckdb_scalar_function_set_name(function_alias, "hillclimbing");
    
    param_type = duckdb_create_logical_type(DUCKDB_TYPE_VARCHAR);
    duckdb_scalar_function_add_parameter(function_alias, param_type);
    
    ret_type = duckdb_create_logical_type(DUCKDB_TYPE_VARCHAR);
    duckdb_scalar_function_set_return_type(function_alias, ret_type);
    
    duckdb_destroy_logical_type(&param_type);
    duckdb_destroy_logical_type(&ret_type);
    
    duckdb_scalar_function_set_function(function_alias, HillclimbingOptimize);
    
    duckdb_register_scalar_function(connection, function_alias);
    duckdb_destroy_scalar_function(&function_alias);
}

// C-compatible entry point
DUCKDB_EXTENSION_ENTRYPOINT(duckdb_connection connection, duckdb_extension_info info, struct duckdb_extension_access *access) {
    RegisterHillclimbingFunction(connection);
    return true;
}
