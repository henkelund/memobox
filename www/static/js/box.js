(function(exports, ng) {
'use strict';

    /**
     * @var Object box
     */
    var box = exports.box = ng.module('box', ['ngResource']);

    /**
     * Configure the box app
     */
    box.config(function($routeProvider) {
        $routeProvider.when('/', {
            controller: 'FileCtrl',
            templateUrl: '/templates/files.html'
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function($resource) {

        /**
         *
         */
        var FileService = function()
        {
            this.filesResource = $resource('/files');
            this.filterResource = $resource('/files/filters');
            this.files = [];
            this.filters = [];
        }
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function(resource)
            {
                this.files = resource.files;
                console.log(resource.sql);
            },

            /**
             * Successful filters load callback
             */
            loadFiltersSuccess: function(data)
            {
                this.filters = data.filters;
            },

            /**
             * Failed load callback
             */
            loadError: function(data)
            {
                console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function(filter)
            {
                var args = {}, fk, vk; // arguments, filter key, value key

                if (typeof filter == 'object') {
                    for (fk in filter) {
                        if (!filter[fk].length) {
                            continue;
                        } else {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    this.loadFilesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load available filters
             */
            loadFilters: function()
            {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            }
        };

        return new FileService();
    });

    /**
     * File controller
     */
    box.controller('FileCtrl', function($scope, FileService) {

        var that = this;
        this.fileService = FileService.loadFilters().loadFiles();
        this.filterState = {};

        /**
         * Check if a given filter option is active
         */
        this.isFilterActive = function(filter, value) {
            var state = that.filterState[filter.param];
            return (typeof state != 'undefined') && state.indexOf(value) >= 0;
        };

        /**
         * Toggle a given filter option
         */
        this.filterClicked = function(filter, value) {
            var i, state = that.filterState[filter.param];
            if (typeof state == 'undefined') {
                state = that.filterState[filter.param] = [];
            }
            if ((i = state.indexOf(value)) >= 0) {
                state.splice(i, 1);
            } else {
                if (typeof filter.multi == 'undefined' || !filter.multi) {
                    state = [];
                }
                state.push(value);
            }
            that.fileService.loadFiles(that.filterState);
        };

        return $scope.FileCtrl = this;
    });

})(window, angular);

