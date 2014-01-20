(function (exports, ng, $, console) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	box.controller('DemoController', function($scope, Reddit) {
	  $scope.reddit = new Reddit();

	  $scope.render = function(e) {
	    return $(e).html();
	  }
    	  
	});
	
	// Reddit constructor function to encapsulate HTTP and pagination logic
	box.factory('Reddit', function($http) {
	  var Reddit = function() {
	    this.images = [];
	    this.busy = false;
	    this.after = 1;
	  };
	
	  Reddit.prototype.nextPage = function() {
	    if (this.busy) return;
	    this.busy = true;
	
		$.ajax({
		    url : "/files?after="+this.after,
			async: false,
			context: this,
		    success : function(result){
			    for(var i = 0; i < result.files.length; i++) {
			      this.images.push({html:"<div class=\"thumbnail\"><div style=\"cursor: pointer;\" onClick=\"window.location.hash = '/files/"+result.files[i]._id+"'\" class=\"preview\" file-thumbnail><div style=\"cursor: pointer; background-image: url(/static/images/thumbnails/260x260/I/M/"+result.files[i].name+"); background-position: 50% 50%;\" onclick=\"window.location.hash = '/files/"+result.files[i]._id+"'\" class=\"preview image\"><img alt=\"image/jpeg\" title=\"image/jpeg\" src=\"/static/images/icons/mint/48/image-jpeg.png\" style=\"display: none;\"></div></div></div>"});
			    }			    

		        this.after = this.after + 1;
		        this.busy = false;
		    }
		});
	  };
	
	  return Reddit;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');

        $stateProvider
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
            .state('files.detail', {
                url: '^/files/:id',
                resolve: {
                    fileDetails: function ($stateParams, FileService) {
                        return FileService.loadDetails($stateParams['id']);
                    }
                },
                controller: 'FilesDetailCtrl',
                templateUrl: '/templates/files.detail.html'
            });
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {

        ng.element($window).bind('scroll', function () {
            var winHeight = $($window).height();
            $('.preview.image').each(function () {
                var rect = this.getBoundingClientRect(),
                    el = $(this),
                    pos,
                    percent;
                if (rect.bottom >= 0 && rect.top <= winHeight) {
                    pos = rect.top / (winHeight - el.height());
                    percent = Math.round(Math.min(100, Math.max(0,
                                pos * 100)));
                    el.css('backgroundPosition', '50% ' + percent + '%');
                }
            });
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.filesResource = $resource('/files');
            this.filterResource = $resource('/files/filters');
            this.detailsResource = $resource('/files/details');
            this.files = [];
            this.filters = [];
            this.details = [];
        };
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function (resource) {
                this.files = resource.files;
                console.log(resource.sql);
            },

            /**
             * Successful filters load callback
             */
            loadFiltersSuccess: function (data) {
                this.filters = data.filters;
            },

            /**
             * Successful filters load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key

                if ($window.devicePixelRatio && $window.devicePixelRatio > 1) {
                    args.retina = 1;
                }

                if (typeof filter === 'object') {
                    for (fk in filter) {
                        if (filter.hasOwnProperty(fk) && filter[fk].length) {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    function (data) {
                        that.loadFilesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },

            /**
             * Load available filters
             */
            loadFilters: function () {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * File thumbnail directive
     */
    box.directive('fileThumbnail', function ($window) {
        return {
            restrict: 'A',
            link: function (scope, element) {
                var el = ng.element(element),
                    file = scope.file,
                    imgUrl = '/static/images/';
                if (file.thumbnail) {
                    el.addClass('image')
                        .css('backgroundImage',
                                'url(' + imgUrl + file.thumbnail + ')')
			.find('img').attr('src', imgUrl + file.icon_small).hide();
			$($window).scroll(); // provoke background re-positioning
                } else {
                    el.addClass('icon')
                        .find('img').attr('src', imgUrl + file.icon_large);
                }
            }
        };
    });

    /**
     * File tooltip directive
     */
    box.directive('fileTooltip', function () {
        return {
            restrict: 'A',
            link: function (scope, element) {
                var file = scope.file;
                $(element).tooltip({
                    title: file.devpath + '/' + file.name+file.extension,
                    placement: 'top'
                });
            }
        };
    });

    /**
     * Available filters filter
     */
    box.filter('availableFilters', function () {
        return function (filters, scope) {
            if (scope.FilesCtrl === undefined) {
                return filters;
            }
            return $.grep(filters, function (item) {
                return scope.FilesCtrl.isFilterAvailable(item);
            });
        };
    });

    /**
     * Active filters filter
     */
    box.filter('activeFilters', function () {
        return function (filters, scope) {
            if (scope.FilesCtrl === undefined) {
                return filters;
            }
            return $.grep(filters, function (item) {
                return scope.FilesCtrl.isFilterActive(item);
            });
        };
    });

    /**
     * Active filter options filter
     */
    box.filter('activeFilterOptions', function () {
        return function (options, filter, scope) {
            var value,
                result = {};
            if (scope.FilesCtrl === undefined) {
                return options;
            }
            for (value in options) {
                if (options.hasOwnProperty(value) &&
                        scope.FilesCtrl.isFilterActive(filter, value)) {
                    result[value] = options[value];
                }
            }
            return result;
        };
    });

    /**
     * File extension trim filter
     */
    box.filter('trimFileExtension', function () {
        return function (fileName) {
            var parts = fileName.split('.');
            if (parts.length >= 2) {
                parts.pop();
            }
            return parts.join('.');
        };
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $location, FileService) {

        var that = this;
        this.fileService = FileService.loadFilters().loadFiles();
        this.filterState = {};
        this.isFilterPending = false;
        $('#filesDetailModal').modal({show: false})
                .on('hide.bs.modal', function () {
            $location.path('/');
            $scope.$apply();
        });

        /**
         * Check if a given filter - or option - is active
         */
        this.isFilterActive = function (filter, value) {
            var state;
            if (filter === undefined) {
                for (state in that.filterState) {
                    if (that.filterState.hasOwnProperty(state) &&
                            that.filterState[state].length > 0) {
                        return true;
                    }
                }
                return false;
            }
            state = that.filterState[filter.param];
            return (state !== undefined) &&
                        (state.length > 0) &&
                        (value === undefined ||
                            state.indexOf(value) >= 0);
        };

        /**
         * Check if a given filter - or option - is available
         */
        this.isFilterAvailable = function (filter, value) {
            var i,
                val;

            if (filter === undefined) {
                filter = that.fileService.filters;
            } else {
                filter = [filter];
            }

            if (value === undefined) {
                for (i = 0; i < filter.length; ++i) {
                    for (val in filter[i].options) {
                        if (filter[i].options.hasOwnProperty(val) &&
                                !that.isFilterActive(filter[i], val)) {
                            return true;
                        }
                    }
                }
                return false;
            }

            for (i = 0; i < filter.length; ++i) {
                if (!that.isFilterActive(filter[i], value)) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Toggle a given filter option
         */
        this.filterClicked = function (filter, value) {
            var i, state = that.filterState[filter.param];
            if (state === undefined) {
                state = that.filterState[filter.param] = [];
            }
            i = state.indexOf(value);
            if (i >= 0) {
                state.splice(i, 1);
            } else {
                if (filter.multi === undefined || !filter.multi) {
                    state = [];
                }
                state.push(value);
            }
            that.isFilterPending = true;
            that.fileService.loadFiles(that.filterState, function () {
                that.isFilterPending = false;
            });
        };

        $scope.FilesCtrl = this;
        return this;
    });

    /**
     * Files detail controller
     */
    box.controller('FilesDetailCtrl', function ($scope, $stateParams, $filter, FileService) {

        this.id = $stateParams['id'];
        this.details = FileService.getDetails(this.id);

		var ts = new Date(null);
		ts.setTime(this.details.timestamp*1000);

        $('#filesDetailModalLabel').html($filter('trimFileExtension')(this.details.name)+" - "+ts.getFullYear().toString() + "-"+ (ts.getMonth()+1) +"-"+ ts.getDate().toString());
        $('#filesDetailModal').modal('show');

        $scope.FilesDetailCtrl = this;
        return this;
    });

}(window, angular, jQuery, console || {log: function () { 'use strict'; return; }}));

